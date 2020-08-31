#########################################################
# Skills
# RESTFul API : Flask, MongoDB, Docker, OOP
#########################################################


#######################################################################
# RESTFul API to handle basic bank transactions (via Postman)
#
# CRUD: Creation, Read, Update, Delete
# Creation (post)
# /register: register a new user (username, password)
# Read
# /users: list all registered users (get)
# /balance: balance of an account (post: username, password)
# Update (post)
# /deposit : deposit (username, password, amount), fee applied
# /transfer : transfer (username, password, to, amount), fee applied
# /takeloan : take a loan from the "BANK" (username, password, amount)
# /payloan : reimburse full or part (username, password, amount)
# Delete
# /del : delete an user (username)
# 
# Each user, including "BANK",
# has "Username", "Password", "Own", "Debt" attributes
# The "BANK" user must be registered before any deposit or transfer
# operation to take place.
#######################################################################
from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt

#########################################################
########### Initialize the API ##########################
#########################################################
app = Flask(__name__)
api = Api(app)

#########################################################
########### Set up the database ########################
#########################################################
client = MongoClient("mongodb://db:27017")  # default port
db = client.BankAPI  # db name
users = db["Users"]  # setup the collection Users

#########################################################
########### Define helper functions #####################
#########################################################
def userExists(username):
    return users.find({"Username": username}).count() != 0


def correctPw(username, password):
    if not userExists(username):
        return False
    # retrieve the hashed password
    hashed_pw = users.find({"Username": username})[0]["Password"]
    return bcrypt.hashpw(password.encode("utf8"), hashed_pw) == hashed_pw


def getUserOwn(username):
    return users.find({"Username": username})[0]["Own"]


def getUserDebt(username):
    return users.find({"Username": username})[0]["Debt"]


def generateStatus(status, msg):
    retJson = {"status": status, "message": msg}
    return retJson


# returns Error dictionary, True / False
def checkCredentials(username, password):
    if not userExists(username):
        return generateStatus(301, "Invalid Username"), True

    if not correctPw(username, password):
        return generateStatus(302, "Incorrect Password"), True

    return None, False  # no error, and the error dictionary is None


def updateOwn(username, balance):
    users.update({"Username": username}, {"$set": {"Own": balance}})


def updateDebt(username, balance):
    users.update({"Username": username}, {"$set": {"Debt": balance}})


def deleteUser(username):
    users.delete_one({"Username": username})


#########################################################
########### Define the resources ########################
#########################################################
class Register(Resource):
    def post(self):
        # Get posted data (on Postman)
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        if userExists(username):
            return jsonify(generateStatus(301, "Username already used"))

        hashed_pw = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())

        # Register the user on the database
        users.insert({"Username": username, "Password": hashed_pw, "Own": 0, "Debt": 0})

        return jsonify(generateStatus(200, "Successful signed up"))


class Users(Resource):
    def get(self):
        list_all = users.distinct("Username")
        retJson = {"status": 200, "users": str(list_all)}
        return jsonify(retJson)


class Balance(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        retJson, error = checkCredentials(username, password)
        if error:
            return jsonify(retJson)

        # projection : returns everything but _id & password
        retJson = users.find({"Username": username}, {"Password": 0, "_id": 0})[0]
        return jsonify(retJson)
    
    
class Deposit(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        amount = postedData["amount"]

        retJson, error = checkCredentials(username, password)
        if error:
            return jsonify(retJson)

        if amount <= 0:
            return jsonify(generateStatus(303, "The amount entered must be positive"))

        own = getUserOwn(username)

        # Transaction fee
        fee = 1

        # Add transaction fee to bank account
        bank_credit = getUserOwn("BANK")
        updateOwn("BANK", bank_credit + fee)

        # Update user account with amount
        updateOwn(username, own + amount - fee)

        return jsonify(generateStatus(200, "Amount added to account"))


class Transfer(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        toAccount = postedData["to"]
        amount = postedData["amount"]

        retJson, error = checkCredentials(username, password)
        if error:
            return jsonify(retJson)

        own = getUserOwn(username)
        if own <= 0:
            return jsonify(generateStatus(304, "Please make a deposit or take a loan"))

        if amount <= 0:
            return jsonify(generateStatus(303, "The amount entered must be positive"))

        if own < amount:
            return jsonify(
                generateStatus(305, "Not enough money for the requested amount")
            )

        if not userExists(toAccount):
            return jsonify(generateStatus(301, "Received account does not exist"))

        own_from = getUserOwn(username)
        own_to = getUserOwn(toAccount)
        own_bank = getUserOwn("BANK")

        # Transaction fee
        fee = 1

        updateOwn("BANK", own_bank + fee)
        updateOwn(toAccount, own_to + amount - fee)
        updateOwn(username, own_from - amount)

        return jsonify(generateStatus(200, "Amount added to account"))


class TakeLoan(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        amount = postedData["amount"]

        retJson, error = checkCredentials(username, password)
        if error:
            return jsonify(retJson)

        if amount <= 0:
            return jsonify(generateStatus(303, "The amount entered must be positive"))

        own = getUserOwn(username)
        debt = getUserDebt(username)
        updateOwn(username, own + amount)
        updateDebt(username, debt + amount)

        return jsonify(generateStatus(200, "Loan added to your Account"))


class PayLoan(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        amount = postedData["amount"]

        retJson, error = checkCredentials(username, password)
        if error:
            return jsonify(retJson)

        own = getUserOwn(username)
        debt = getUserDebt(username)

        if debt <= 0:
            return jsonify(generateStatus(306, "You don't have any loan to pay back"))

        if debt < amount:
            return jsonify(
                generateStatus(307, "The requested amount is greater than the loan")
            )

        if own < amount:
            return jsonify(
                generateStatus(305, "Not enough money for the requested amount")
            )

        updateOwn(username, own - amount)
        updateDebt(username, debt - amount)

        return jsonify(generateStatus(200, "Loan paid"))


class Delete(Resource):
    def delete(self):
        postedData = request.get_json()
        username = postedData["username"]
        if userExists(username):
            deleteUser(postedData["username"])
            return jsonify(generateStatus(200, "User deleted"))
        
        return jsonify(generateStatus(301, "Invalid Username"))



#########################################################
##### Route the resources to the paths (Postman) ########
#########################################################
api.add_resource(Register, "/register")
api.add_resource(Users, "/users")
api.add_resource(Balance, "/balance")
api.add_resource(Deposit, "/deposit")
api.add_resource(Transfer, "/transfer")
api.add_resource(TakeLoan, "/takeloan")
api.add_resource(PayLoan, "/payloan")
api.add_resource(Delete, "/delete")

#########################################################
########### Run app.py on Docker local host #############
#########################################################
if __name__ == "__main__":
    app.run(host="0.0.0.0")