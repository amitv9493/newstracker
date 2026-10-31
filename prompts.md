1. scaffold this project using fastapi, alembic boilerplate code with sqlalchemy and celery connection. Follow the MVC arch with service layer. Create one health endpoint and one to trigger a celery task upon POSTing an endpoint. Integrate the general exception handlers in the Fastapi app. 
2. create a dependencies.py file, add thefastapi related deps that can be used in the route handler, ie database sessions and can will be passed down to the srevice layer,
3. add resusable pagination feature in this project. 
4. db related error such as integrity error, conflicterror should not be handled in the service layer they should be handled separetely.
5. use pydantic settings to read the env from the .env vars do not use os,environ or os.getenv.

