# api/business.py
# import json
# from fastapi import APIRouter, Depends, HTTPException, Body
# from fastapi.security import OAuth2PasswordBearer
# from core import security, db
# from core.logger import logger
# from core.security import encrypt_password, decrypt_password
# from models import business_models, db_models
# from sqlmodel import Session, select
# from ldap3 import Server, Connection, ALL, core, MODIFY_REPLACE, MODIFY_ADD, MODIFY_DELETE
# from jose import JWTError
# from .dependencies import get_current_user

# router = APIRouter()

# # List connections
# @router.get("/connections", response_model=list[business_models.ConnectionOut])
# def list_connections(user: db_models.IdentityUser = Depends(get_current_user), session: Session = Depends(db.get_session)):
#     result = session.exec(select(db_models.LDAPConnection).where(db_models.LDAPConnection.user_id == user.id)).all()
#     return result

# # Create LDAP connection
# @router.post("/connections")
# def create_connection(conn: business_models.ConnectionCreate, user: db_models.IdentityUser = Depends(get_current_user), session: Session = Depends(db.get_session)):
#     logger.info(f"User '{user.subject}' creating LDAP connection '{conn.name}' ({conn.hostname}:{conn.port}, SSL={conn.use_ssl})")

#     existing = session.exec(
#         select(db_models.LDAPConnection).where(
#             (db_models.LDAPConnection.user_id == user.id) &
#             (db_models.LDAPConnection.name == conn.name)
#         )
#     ).first()
#     if existing:
#         raise HTTPException(status_code=400, detail="Connection name already exists")

#     try:
#         server = Server(conn.hostname, port=conn.port, use_ssl=conn.use_ssl, get_info=ALL)
#         test_conn = Connection(server, user=conn.bind_dn, password=conn.password, auto_bind=True)
#         test_conn.unbind()
#     except core.exceptions.LDAPException as e:
#         raise HTTPException(status_code=400, detail=f"LDAP error: {str(e)}")
    
#     encrypted_pw = encrypt_password(conn.password)

#     new_conn = db_models.LDAPConnection(
#         user_id=user.id,
#         name=conn.name,
#         hostname=conn.hostname,
#         port=conn.port,
#         bind_dn=conn.bind_dn,
#         encrypted_password=encrypted_pw,
#         use_ssl=conn.use_ssl
#     )
#     session.add(new_conn)
#     session.commit()
#     session.refresh(new_conn)
#     return {"msg": "Connection created", "id": new_conn.id}

# # Update LDAP connection
# @router.patch("/connections/{conn_id}")
# def patch_connection(
#     conn_id: int,
#     conn_update: business_models.ConnectionUpdate,
#     user: db_models.IdentityUser = Depends(get_current_user),
#     session: Session = Depends(db.get_session)
# ):
#     conn_entry = session.exec(
#         select(db_models.LDAPConnection).where(
#             (db_models.LDAPConnection.id == conn_id) &
#             (db_models.LDAPConnection.user_id == user.id)
#         )
#     ).first()

#     if not conn_entry:
#         raise HTTPException(status_code=404, detail="Connection not found")

#     # Determine fields being updated
#     updates = conn_update.model_dump(exclude_unset=True)
#     needs_validation = any(f in updates for f in {"name", "hostname", "port", "bind_dn", "password", "use_ssl"})

#     # Attempt connection test if needed
#     if needs_validation:
#         try:
#             hostname = updates.get("hostname", conn_entry.hostname)
#             port = updates.get("port", conn_entry.port)
#             bind_dn = updates.get("bind_dn", conn_entry.bind_dn)
#             password = updates.get("password")
#             use_ssl = updates.get("use_ssl", conn_entry.use_ssl)

#             # Decrypt existing if no new password
#             ldap_password = password if password is not None else decrypt_password(conn_entry.encrypted_password)

#             server = Server(hostname, port=port, use_ssl=use_ssl, get_info=ALL)
#             test_conn = Connection(server, user=bind_dn, password=ldap_password, auto_bind=True)
#             test_conn.unbind()
#         except core.exceptions.LDAPException as e:
#             raise HTTPException(status_code=400, detail=f"LDAP validation failed: {str(e)}")

#     # Apply updates
#     for key, value in updates.items():
#         if key == "password":
#             setattr(conn_entry, "encrypted_password", encrypt_password(value))
#         else:
#             setattr(conn_entry, key, value)

#     session.add(conn_entry)
#     session.commit()
#     session.refresh(conn_entry)
#     return {"msg": "Connection updated", "id": conn_entry.id}

# # Delete LDAP connection
# @router.delete("/connections/{conn_id}")
# def delete_connection(
#     conn_id: int,
#     user: db_models.IdentityUser = Depends(get_current_user),
#     session: Session = Depends(db.get_session)
# ):
#     conn_entry = session.exec(
#         select(db_models.LDAPConnection).where(
#             (db_models.LDAPConnection.id == conn_id) &
#             (db_models.LDAPConnection.user_id == user.id)
#         )
#     ).first()

#     if not conn_entry:
#         raise HTTPException(status_code=404, detail="Connection not found")

#     session.delete(conn_entry)
#     session.commit()
#     return {"msg": "Connection deleted"}

# # LDAP Search API
# @router.post("/ldap/search")
# def ldap_search(req: business_models.LDAPSearchRequest, user: db_models.IdentityUser = Depends(get_current_user), session: Session = Depends(db.get_session)):
#     conn_entry = session.exec(
#         select(db_models.LDAPConnection).where(
#             (db_models.LDAPConnection.id == req.connection_id) &
#             (db_models.LDAPConnection.user_id == user.id)
#         )
#     ).first()

#     if not conn_entry:
#         raise HTTPException(status_code=404, detail="Connection not found")

#     logger.info(f"User '{user.subject}' performing LDAP search on connection '{conn_entry.name}' base_dn='{req.base_dn}' filter='{req.filter}'")

#     try:
#         server = Server(conn_entry.hostname, port=conn_entry.port, use_ssl=conn_entry.use_ssl, get_info=ALL)
#         ldap_conn = Connection(server, user=conn_entry.bind_dn, password=decrypt_password(conn_entry.encrypted_password), auto_bind=True)

#         ldap_conn.search(search_base=req.base_dn, search_filter=req.filter, attributes=req.attributes)
#         results = [
#             {
#                 "dn": entry.entry_dn,
#                 "attributes": entry.entry_attributes_as_dict
#             }
#             for entry in ldap_conn.entries
#         ]
#         ldap_conn.unbind()

#         return results
#     except core.exceptions.LDAPException as e:
#         logger.error(f"LDAP search error: {e}")
#         raise HTTPException(status_code=400, detail=f"LDAP search failed: {str(e)}")

# # LDAP Modify API
# @router.post("/ldap/modify")
# def ldap_modify(req: business_models.LDAPModifyRequest, user: db_models.IdentityUser = Depends(get_current_user), session: Session = Depends(db.get_session)):
#     conn_entry = session.exec(
#         select(db_models.LDAPConnection).where(
#             (db_models.LDAPConnection.id == req.connection_id) &
#             (db_models.LDAPConnection.user_id == user.id)
#         )
#     ).first()

#     if not conn_entry:
#         raise HTTPException(status_code=404, detail="Connection not found")
#     logger.info(f"User '{user.subject}' performing LDAP modify on DN '{req.dn}' using connection '{conn_entry.name}'")

#     try:
#         server = Server(conn_entry.hostname, port=conn_entry.port, use_ssl=conn_entry.use_ssl, get_info=ALL)
#         ldap_conn = Connection(server, user=conn_entry.bind_dn, password=decrypt_password(conn_entry.encrypted_password), auto_bind=True)

#         changes = {}
#         for change in req.changes:
#             operation = change.get("operation")
#             attr = change.get("attribute")
#             values = change.get("values")

#             op_map = {
#                 "replace": MODIFY_REPLACE,
#                 "add": MODIFY_ADD,
#                 "delete": MODIFY_DELETE
#             }

#             if operation not in op_map:
#                 raise HTTPException(status_code=400, detail=f"Invalid operation: {operation}")

#             changes[attr] = (op_map[operation], values)

#         success = ldap_conn.modify(req.dn, changes)
#         ldap_conn.unbind()

#         if not success:
#             logger.error(f"LDAP modify failed: {ldap_conn.result}")
#             raise HTTPException(status_code=400, detail=f"LDAP modify failed: {ldap_conn.result.get('message', 'Unknown error')}")

#         return {"msg": "Modify successful"}

#     except core.exceptions.LDAPException as e:
#         logger.error(f"LDAP modify error: {e}")
#         raise HTTPException(status_code=400, detail=f"LDAP modify failed: {str(e)}")
