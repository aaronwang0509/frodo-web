# core/services/esv_sync_service.py
from sqlmodel import Session, select
from typing import List, Dict, Any
from core.logger import get_logger
from core.frodo.sync_esv import pull_variables_from_local
from models import db_models
from models.esv_models import EsvVariableResponse, EsvVariableCreate, EsvVariableUpdate, EsvVariableDelete

logger = get_logger(__name__)

def build_esv_variable_response(
    var: db_models.EsvVariable,
    session: Session
) -> EsvVariableResponse:
    """
    Build a single EsvVariableResponse for the given EsvVariable,
    collecting its values per environment.
    """
    values_lookup = {}
    for val in var.values:
        env = session.get(db_models.Environment, val.environment_id)
        if env:
            values_lookup[env.name] = val.value

    return EsvVariableResponse(
        name=var.name,
        description=var.description,
        expressionType=var.expressionType,
        values=values_lookup
    )

def diff_repo_vs_db_all_envs(
    paic_config_path: str,
    session: Session,
    current_user: db_models.UserProfile
) -> Dict[str, Any]:
    """
    Diff all envs in local repo vs DB for the user.
    Returns dict with 'create', 'update', 'delete' lists.
    """

    # Gather all envs for this user
    envs = session.exec(
        select(db_models.Environment).where(
            db_models.Environment.user_profile_id == current_user.id
        )
    ).all()

    if not envs:
        raise ValueError("No environments found for current user.")

    # Build repo_lookup
    repo_lookup = {}
    for env in envs:
        repo_data = pull_variables_from_local(paic_config_path, env.name)
        for name, var in repo_data.items():
            if name not in repo_lookup:
                repo_lookup[name] = {
                    "description": var.get("description"),
                    "expressionType": var.get("expressionType"),
                    "values": {}
                }
            repo_lookup[name]["values"][env.name] = var.get("value")

    # Build db_lookup
    db_vars = session.exec(
        select(db_models.EsvVariable).where(
            db_models.EsvVariable.user_profile_id == current_user.id
        )
    ).all()

    db_lookup = { var.name: var for var in db_vars }

    create_list = []
    update_list = []
    delete_list = []

    # Compare repo → DB
    for name, repo_var in repo_lookup.items():
        if name not in db_lookup:
            # Variable does not exist in DB → create
            create_list.append({
                "name": name,
                "description": repo_var["description"],
                "expressionType": repo_var["expressionType"],
                "values": repo_var["values"]
            })
        else:
            db_var = db_lookup[name]
            diff_description = None
            diff_expressionType = None

            if db_var.description != repo_var["description"]:
                diff_description = {"old": db_var.description, "new": repo_var["description"]}

            if db_var.expressionType != repo_var["expressionType"]:
                diff_expressionType = {"old": db_var.expressionType, "new": repo_var["expressionType"]}

            changed_values = {}
            partial_create_values = {}

            for env_name, repo_val in repo_var["values"].items():
                env_obj = next((e for e in envs if e.name == env_name), None)
                if not env_obj:
                    continue

                db_val = next(
                    (v for v in db_var.values if v.environment_id == env_obj.id),
                    None
                )
                db_val_value = db_val.value if db_val else None

                if db_val_value is None and repo_val is not None:
                    # New env value that didn't exist in DB → partial create
                    partial_create_values[env_name] = repo_val
                elif db_val_value != repo_val:
                    # Value exists but changed → update
                    changed_values[env_name] = {"old": db_val_value, "new": repo_val}

            if diff_description or diff_expressionType or changed_values:
                if not changed_values:
                    # Include all unchanged env values
                    unchanged_values = {
                        env_name: repo_var["values"].get(env_name)
                        for env_name in repo_var["values"].keys()
                    }
                    update_list.append({
                        "name": name,
                        "description": diff_description if diff_description else repo_var["description"],
                        "expressionType": diff_expressionType if diff_expressionType else repo_var["expressionType"],
                        "values": unchanged_values
                    })
                else:
                    update_list.append({
                        "name": name,
                        "description": diff_description if diff_description else repo_var["description"],
                        "expressionType": diff_expressionType if diff_expressionType else repo_var["expressionType"],
                        "values": changed_values
                    })

            if partial_create_values:
                create_list.append({
                    "name": name,
                    "description": repo_var["description"],
                    "expressionType": repo_var["expressionType"],
                    "values": partial_create_values
                })

    # Vars in DB but not in repo → delete (including partial deletes)
    for name, db_var in db_lookup.items():
        if name not in repo_lookup:
            delete_list.append({
                "name": db_var.name,
                "description": db_var.description,
                "expressionType": db_var.expressionType,
                "values": {
                    env.name: val.value for val in db_var.values
                    for env in envs if env.id == val.environment_id
                }
            })
        else:
            repo_envs = repo_lookup[name]["values"].keys()
            partial_values = {}
            for db_val in db_var.values:
                env_obj = next((e for e in envs if e.id == db_val.environment_id), None)
                if env_obj and env_obj.name not in repo_envs:
                    partial_values[env_obj.name] = db_val.value

            if partial_values:
                delete_list.append({
                    "name": db_var.name,
                    "description": db_var.description,
                    "expressionType": db_var.expressionType,
                    "values": partial_values
                })

    return {
        "create": create_list,
        "update": update_list,
        "delete": delete_list
    }

def diff_db_vs_repo_all_envs(
    paic_config_path: str,
    session: Session,
    current_user: db_models.UserProfile
) -> Dict[str, Any]:
    """
    Diff DB (source of truth) vs local repo for all envs.
    Returns dict with 'create', 'update', 'delete' lists.
    """

    envs = session.exec(
        select(db_models.Environment).where(
            db_models.Environment.user_profile_id == current_user.id
        )
    ).all()

    if not envs:
        raise ValueError("No environments found for current user.")

    # Build DB lookup
    db_vars = session.exec(
        select(db_models.EsvVariable).where(
            db_models.EsvVariable.user_profile_id == current_user.id
        )
    ).all()

    db_lookup = {}
    for var in db_vars:
        db_lookup[var.name] = {
            "description": var.description,
            "expressionType": var.expressionType,
            "values": {}
        }
        for val in var.values:
            env_name = next((e.name for e in envs if e.id == val.environment_id), None)
            if env_name:
                db_lookup[var.name]["values"][env_name] = val.value

    # Build repo lookup
    repo_lookup = {}
    for env in envs:
        repo_data = pull_variables_from_local(paic_config_path, env.name)
        for name, var in repo_data.items():
            if name not in repo_lookup:
                repo_lookup[name] = {
                    "description": var.get("description"),
                    "expressionType": var.get("expressionType"),
                    "values": {}
                }
            repo_lookup[name]["values"][env.name] = var.get("value")

    create_list = []
    update_list = []
    delete_list = []

    # DB → Repo
    for name, db_var in db_lookup.items():
        if name not in repo_lookup:
            create_list.append({
                "name": name,
                "description": db_var["description"],
                "expressionType": db_var["expressionType"],
                "values": db_var["values"]
            })
        else:
            repo_var = repo_lookup[name]
            diff_description = None
            diff_expressionType = None

            if db_var["description"] != repo_var["description"]:
                diff_description = {
                    "old": repo_var["description"],
                    "new": db_var["description"]
                }

            if db_var["expressionType"] != repo_var["expressionType"]:
                diff_expressionType = {
                    "old": repo_var["expressionType"],
                    "new": db_var["expressionType"]
                }

            changed_values = {}
            partial_create_values = {}

            for env_name, db_val in db_var["values"].items():
                repo_val = repo_var["values"].get(env_name)

                if repo_val is None:
                    partial_create_values[env_name] = db_val
                elif repo_val != db_val:
                    changed_values[env_name] = {"old": repo_val, "new": db_val}

            if diff_description or diff_expressionType or changed_values:
                if not changed_values:
                    # Include all unchanged env values
                    unchanged_values = {
                        env_name: db_var["values"].get(env_name)
                        for env_name in db_var["values"].keys()
                    }
                    update_list.append({
                        "name": name,
                        "description": diff_description if diff_description else db_var["description"],
                        "expressionType": diff_expressionType if diff_expressionType else db_var["expressionType"],
                        "values": unchanged_values
                    })
                else:
                    update_list.append({
                        "name": name,
                        "description": diff_description if diff_description else db_var["description"],
                        "expressionType": diff_expressionType if diff_expressionType else db_var["expressionType"],
                        "values": changed_values
                    })

            if partial_create_values:
                create_list.append({
                    "name": name,
                    "description": db_var["description"],
                    "expressionType": db_var["expressionType"],
                    "values": partial_create_values
                })

    # Vars in repo but not in DB → delete (including partial env deletes)
    for name, repo_var in repo_lookup.items():
        if name not in db_lookup:
            delete_list.append({
                "name": name,
                "description": repo_var["description"],
                "expressionType": repo_var["expressionType"],
                "values": repo_var["values"]
            })
        else:
            db_envs = db_lookup[name]["values"].keys()
            partial_values = {}
            for env_name, repo_val in repo_var["values"].items():
                if env_name not in db_envs:
                    partial_values[env_name] = repo_val

            if partial_values:
                delete_list.append({
                    "name": name,
                    "description": repo_var["description"],
                    "expressionType": repo_var["expressionType"],
                    "values": partial_values
                })

    return {
        "create": create_list,
        "update": update_list,
        "delete": delete_list
    }

def get_variables_in_db(
    session: Session,
    current_user: db_models.UserProfile
) -> List[EsvVariableResponse]:
    """
    Get all ESV variables for the current user, grouped with values per environment.
    """
    logger.info(f"Fetching ESV variables for user_id={current_user.id}")
    variables = session.exec(
        select(db_models.EsvVariable).where(
            db_models.EsvVariable.user_profile_id == current_user.id
        )
    ).all()

    response = [build_esv_variable_response(var, session) for var in variables]

    logger.info(f"Found {len(response)} ESV variables for user_id={current_user.id}")
    return response

def create_variables_in_db(
    payload: List[EsvVariableCreate],
    session: Session,
    current_user: db_models.UserProfile
) -> List[EsvVariableResponse]:
    logger.info(f"Starting create_variables_in_db with {len(payload)} items for user_id={current_user.id}")
    response = []

    for item in payload:
        var = session.exec(
            select(db_models.EsvVariable).where(
                db_models.EsvVariable.name == item.name,
                db_models.EsvVariable.user_profile_id == current_user.id
            )
        ).first()

        if not var:
            logger.info(f"Creating new variable: {item.name}")
            var = db_models.EsvVariable(
                name=item.name,
                description=item.description,
                expressionType=item.expressionType,
                user_profile_id=current_user.id
            )
            session.add(var)
            session.flush()

        if not item.values:
            logger.warning(f"Skipping variable {item.name}: no values provided.")
            continue

        for env_name, value in item.values.items():
            env = session.exec(
                select(db_models.Environment).where(
                    db_models.Environment.name == env_name,
                    db_models.Environment.user_profile_id == current_user.id
                )
            ).first()

            if not env:
                continue

            val_obj = session.exec(
                select(db_models.EsvVariableValue).where(
                    db_models.EsvVariableValue.variable_id == var.id,
                    db_models.EsvVariableValue.environment_id == env.id
                )
            ).first()

            if not val_obj:
                val_obj = db_models.EsvVariableValue(
                    variable_id=var.id,
                    environment_id=env.id,
                    value=value
                )
                session.add(val_obj)

        logger.info(f"Finished processing variable: {item.name}")

        response.append(build_esv_variable_response(var, session))

    session.commit()
    logger.info(f"Committed {len(response)} ESV variables for user_id={current_user.id}")
    return response

def update_variables_in_db(
    payload: List[EsvVariableUpdate],
    session: Session,
    current_user: db_models.UserProfile
) -> List[EsvVariableResponse]:
    logger.info(f"Starting update_variables_in_db with {len(payload)} items for user_id={current_user.id}")
    response = []

    for item in payload:
        var = session.exec(
            select(db_models.EsvVariable).where(
                db_models.EsvVariable.name == item.name,
                db_models.EsvVariable.user_profile_id == current_user.id
            )
        ).first()

        if not var:
            logger.warning(f"Variable {item.name} not found. Skipping.")
            continue

        # Update base fields
        if item.description is not None:
            var.description = item.description
        if item.expressionType is not None:
            var.expressionType = item.expressionType

        if item.values:
            for env_name, new_value in item.values.items():
                env = session.exec(
                    select(db_models.Environment).where(
                        db_models.Environment.name == env_name,
                        db_models.Environment.user_profile_id == current_user.id
                    )
                ).first()

                if not env:
                    logger.warning(f"Environment {env_name} not found for user. Skipping value.")
                    continue

                val_obj = session.exec(
                    select(db_models.EsvVariableValue).where(
                        db_models.EsvVariableValue.variable_id == var.id,
                        db_models.EsvVariableValue.environment_id == env.id
                    )
                ).first()

                if val_obj:
                    val_obj.value = new_value
                else:
                    logger.warning(f"Value for env {env_name} does not exist for variable {item.name}. Skipping. Please use create instead.")
                    continue

        logger.info(f"Updated variable: {item.name}")

        response.append(build_esv_variable_response(var, session))

    session.commit()
    logger.info(f"Committed {len(response)} updated ESV variables for user_id={current_user.id}")
    return response

def delete_variables_in_db(
    payload: List[EsvVariableDelete],
    session: Session,
    current_user: db_models.UserProfile
) -> List[EsvVariableResponse]:
    """
    Delete ESV variables or partial variable values for given envs.
    - If 'values' is provided, delete only those env values.
    - If no remaining values, delete the variable too.
    - If no 'values', delete the entire variable.
    """
    logger.info(f"Starting delete_variables_in_db with {len(payload)} items for user_id={current_user.id}")
    response = []

    for item in payload:
        var = session.exec(
            select(db_models.EsvVariable).where(
                db_models.EsvVariable.name == item.name,
                db_models.EsvVariable.user_profile_id == current_user.id
            )
        ).first()

        if not var:
            logger.warning(f"Variable {item.name} not found. Skipping.")
            continue

        # Delete only specified env values if provided
        if item.values:
            for env_name in item.values.keys():
                env = session.exec(
                    select(db_models.Environment).where(
                        db_models.Environment.name == env_name,
                        db_models.Environment.user_profile_id == current_user.id
                    )
                ).first()

                if not env:
                    logger.warning(f"Environment {env_name} not found. Skipping.")
                    continue

                val_obj = session.exec(
                    select(db_models.EsvVariableValue).where(
                        db_models.EsvVariableValue.variable_id == var.id,
                        db_models.EsvVariableValue.environment_id == env.id
                    )
                ).first()

                if val_obj:
                    session.delete(val_obj)
                    logger.info(f"Deleted value for variable {item.name} in env {env_name}.")
                else:
                    logger.info(f"No value to delete for variable {item.name} in env {env_name}.")

        else:
            # No envs specified → delete entire variable + its values
            for val in var.values:
                session.delete(val)
                logger.info(f"Deleted value for variable {item.name} in env_id={val.environment_id}.")

        # After value deletes, check if variable has any remaining values
        remaining_values = session.exec(
            select(db_models.EsvVariableValue).where(
                db_models.EsvVariableValue.variable_id == var.id
            )
        ).all()

        if not remaining_values:
            session.delete(var)
            logger.info(f"Deleted variable {item.name} because no remaining values.")

        # Prepare response with what remains (if any)
        if remaining_values:
            response.append(build_esv_variable_response(var, session))

    session.commit()
    logger.info(f"Committed ESV deletes for user_id={current_user.id}")
    return response