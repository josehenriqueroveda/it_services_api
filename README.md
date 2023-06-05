# IT Services API

This API provides two endpoints for general IT services, as perform automatic ticket categorization for tickets from Sharepoint and GLPI, and control the users in groups from Active Directory.
The first endpoint, `/v1/sharepoint/category`, receives the ticket object from Sharepoint and returns the most relevant category according to the text of the ticket. The second endpoint, `/v1/glpi/category`, receives the ticket object from GLPI and returns the most relevant category according to the text of the ticket. The endpoint `/v1/groups/users` receives a list of users and groups generating a *.csv* file with the users to be updated on Active Directory.

## Installation
To install the API, clone the repository and install the required dependencies:
```bash
git clone https://github.com/josehenriqueroveda/it_services_api.git
cd it_services_api
pip install -r requirements.txt

python -m spacy download pt_core_news_sm
```

## Usage
To start the API server, run the following command:
```bash
uvicorn main:app --reload
```
or
```bash
python main.py
```

This will start the server at http://localhost:8000 or the configured IP and Port.

## Endpoints
### Sharepoint Ticket Categorization
```http
POST /v1/sharepoint/category
```
To make the categorization for a single ticket, send a **POST** request to `/v1/sharepoint/category` with a JSON object containing the ticket data. The following fields are required:
 - `title`: a string with the title of the ticket.
 - `description`: a string with the description of the ticket.

The response will be a string containing the category of the ticket:
```json
  "Network"
```
### GLPI Ticket Categorization
```http
POST /v1/glpi/category
```
To make the categorization for a single ticket, send a **POST** request to `/v1/glpi/category` with a JSON object containing the ticket data. The following fields are required:
 - `title`: a string with the title of the ticket.
 - `description`: a string with the description of the ticket.

The response will be a string containing the category of the ticket:
```json
  "SAP"
```
 ### AD Groups Users
 ```http
POST /v1/groups/users
```
To insert or delete users on the active directory groups, send a **POST** request to the `/v1/groups/users` endpoint with a list of the following JSON payload containing the following fields:
 - email: a string with the email of the user. 
 - group: a string with the name of the group.
 - action: a string with the action to be performed. The possible values are `insert` and `delete`.

The response, in case of success, is a JSON object with the following fields:
```json
{
    "message": "Groups updated successfully!"
}
```

## License
This package is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing
If you find a bug or have a feature request, please open an issue on the repository. If you would like to contribute code, please fork the repository and submit a pull request.

Before submitting a pull request, please make sure that your code adheres to the following guidelines:
 - Follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide.
 - Write docstrings for all functions and classes.
 - Write unit tests for all functions and classes.
 - Make sure that all tests pass by running pytest.
 - Keep the code simple and easy to understand.