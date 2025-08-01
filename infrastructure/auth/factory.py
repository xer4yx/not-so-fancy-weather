from .crypt import Sha256Hash, BcryptHash
from .jwt import JWTAuth
from core.interface import HashInterface, AuthInterface


class AuthFactory:
    @staticmethod
    def create_hash(crypt_algorithm: str) -> HashInterface:
        if crypt_algorithm not in ["sha256", "bcrypt"]:
            raise ValueError("Crypt algorithm not supported")
        
        if crypt_algorithm == "sha256":
            return Sha256Hash()
        
        return BcryptHash()
    
    @staticmethod
    def create_auth() -> AuthInterface:
        return JWTAuth()
