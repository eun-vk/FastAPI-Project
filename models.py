from pydantic import BaseModel

# 회원가입할 때 받을 정보
class UserCreate(BaseModel):
    username: str      # 사용자명 (텍스트)
    email: str         # 이메일 (텍스트)
    password: str      # 비밀번호 (텍스트)

# 로그인할 때 받을 정보
class UserLogin(BaseModel):
    username: str      # 사용자명
    password: str      # 비밀번호

# 실제로 저장할 사용자 정보
class User(BaseModel):
    id: int                    # 사용자 고유번호
    username: str              # 사용자명
    email: str                 # 이메일
    hashed_password: str       # 암호화된 비밀번호

# 다른 사람에게 보여줄 사용자 정보 (비밀번호 제외!)
class UserResponse(BaseModel):
    id: int           # 사용자 고유번호
    username: str     # 사용자명
    email: str        # 이메일
    # 비밀번호는 절대 포함 안 함!
