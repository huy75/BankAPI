# BankAPI
## Installation
```
This program can be use with the commands:
    Docker-compose build
    Docker-compose up
    Postman
```
## Description
```
This is a RESTFul API to handle basic bank transactions (via Postman)

CRUD: Creation, Read, Update, Delete
The endpoints are:
    Creation (post)
        /register: register a new user (username, password)
    Read
        /users: list all registered users (get)
        /balance: balance of an account (post: username, password)
    Update (post)
        /deposit: deposit (username, password, amount), fee applied
        /transfer: transfer (username, password, to, amount), fee applied
        /takeloan: take a loan from the "BANK" (username, password, amount)
        /payloan: reimburse full or part (username, password, amount)
    Delete
        /delete: delete an user (username)

Each user, including "BANK", has "Username", "Password", "Own", "Debt" attributes
The "BANK" user must be registered before any deposit or transfer
operation to take place.
```
## Implementation
```
Flask
flask_restful
pymongo
bcrypt
```
