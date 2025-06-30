# api/esv.py

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from core import db
from core.security import get_current_user
from core.logger import get_logger
from api.settings import settings
from models import db_models
from core.frodo.sync_esv import pull_variables_from_local

logger = get_logger(__name__)

router = APIRouter()

@router.post("/variable/{env_name}/pull", status_code=200)
def pull_esv_variables(
    env_name: str,
    session: Session = Depends(db.get_session),
    current_user: db_models.UserProfile = Depends(get_current_user)
):
    """
    Pull ESV variables from local config repo and save/update them to DB.
    """

    # Find environment for this user
    env = session.exec(
        select(db_models.Environment).where(
            (db_models.Environment.user_profile_id == current_user.id) &
            (db_models.Environment.name == env_name)
        )
    ).first()

    if not env:
        raise HTTPException(status_code=404, detail="Environment not found.")

    logger.info(f"Starting ESV pull for env='{env_name}' user_id={current_user.id}")

    # Use your helper to get the data
    esv_variable_data = pull_variables_from_local(
        paic_config_path=settings.PAIC_CONFIG_PATH,
        env_name=env_name
    )

    logger.info(f"Pulled ESV variable data: {list(esv_variable_data.keys())}")

    for var_name, var_content in esv_variable_data.items():
        # Get or create EsvVariable for this user
        variable = session.exec(
            select(db_models.EsvVariable).where(
                (db_models.EsvVariable.name == var_name) &
                (db_models.EsvVariable.user_profile_id == current_user.id)
            )
        ).first()

        if not variable:
            variable = db_models.EsvVariable(
                name=var_name,
                description=var_content.get("description"),
                expressionType=var_content.get("expressionType"),
                user_profile_id=current_user.id
            )
            session.add(variable)
            logger.info(f"Created new EsvVariable: {var_name}")
        else:
            # Update description & expressionType if changed
            variable.description = var_content.get("description")
            variable.expressionType = var_content.get("expressionType")
            logger.info(f"Updated EsvVariable: {var_name}")

        session.commit()
        session.refresh(variable)

        # Get or create EsvVariableValue for this env
        value_record = session.exec(
            select(db_models.EsvVariableValue).where(
                (db_models.EsvVariableValue.variable_id == variable.id) &
                (db_models.EsvVariableValue.environment_id == env.id)
            )
        ).first()

        if not value_record:
            value_record = db_models.EsvVariableValue(
                variable_id=variable.id,
                environment_id=env.id,
                value=var_content.get("value")
            )
            session.add(value_record)
            logger.info(f"Created new EsvVariableValue for {var_name}")
        else:
            value_record.value = var_content.get("value")
            logger.info(f"Updated EsvVariableValue for {var_name}")

        session.commit()

    logger.info(f"Completed ESV pull for env='{env_name}' user_id={current_user.id}")

    return {
        "detail": f"ESV variables pulled and saved for environment '{env_name}'.",
        "variables_count": len(esv_variable_data)
    }