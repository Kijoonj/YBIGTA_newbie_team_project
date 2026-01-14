from app.user.user_repository import UserRepository
from app.user.user_schema import User, UserLogin, UserUpdate

class UserService:
    def __init__(self, userRepoitory: UserRepository) -> None:
        self.repo = userRepoitory

    def login(self, user_login: UserLogin) -> User:
        """
        Searches user from db by matching e-mail address. 
        Checks:
        1. if the user exists
        2. if the pswd matches
        If so returns the user
        """
        user : User = self.repo.get_user_by_email(user_login.email)
        
        if user is None:
            raise ValueError("User not Found.")
        
        if user.password != user_login.password:
            raise ValueError("Invalid ID/PW")

        return user
        


    def register_user(self, new_user: User) -> User:
        """
        Registers a new user.
        1) If user already exists, raise error
        2) Otherwise save and return the user
        """
        existing_user : User = self.repo.get_user_by_email(new_user.email)
        if existing_user:
            raise ValueError("User already Exists.")

        return self.repo.save_user(new_user)



    def delete_user(self, email: str) -> User:
        """
        Deletes a user.
        1) If user does not exist, raise a error 
        2) Otherwise, delete and return the user
        """        
        delete_user : User = self.repo.get_user_by_email(email)
        if delete_user is None:
            raise ValueError("User not Found.")
        
        return self.repo.delete_user(delete_user)



    def update_user_pwd(self, user_update: UserUpdate) -> User:
        """
        Updates Password for user with matching email
        1) If user is not found, raise a error
        2) Otherwise update pswd and return the user
        """
        update_user : User = self.repo.get_user_by_email(user_update.email)
        if update_user is None:
            raise ValueError("User not Found.")
        
        update_user.password = user_update.new_password

        return self.repo.save_user(update_user)
        