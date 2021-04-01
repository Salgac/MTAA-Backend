# Projekt na predmet mobilné technológie a aplikácie

App deployed on: http://139.162.130.177:8000/

## Link na dokumentáciu

- https://docs.google.com/document/d/1XpzISc90pOp5DxOYALgtJmV85c8TKntzHyB-K1jk4uw/edit?usp=sharing

## Local setup

### On Windows:
1. Install python 3.8.8: https://www.python.org/ftp/python/3.8.8/python-3.8.8-amd64.exe.
2. Clone the project.
3. Run setup.bat in parent directory of the project. The app is automatically starter.
4. You can access the endpoint through swagger http://localhost:8000/swagger/
5. Log in with 
    -   username: test
    -   password: password
6. Copy token and paste it to Authorize in format 'Token (copied token)'.
7. Now you are authorized to all the endpoints.

### On Linux:
1. Install python 3.8
2. Clone the project using: `git clone`.
3. Run setup.sh in parent directory of the project. Ensure you can execute the file using: `chmod x+u setup.sh`. 
4. The script should automatically install all the dependencies and start the app.
5. You can access the endpoint through swagger at http://localhost:8000/swagger/
6. Log in with 
    -   username: test
    -   password: password
7. Copy token and paste it to Authorize in format 'Token (copied token)'.
8. Now you are authorized to all the endpoints.
