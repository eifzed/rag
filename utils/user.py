from fastapi import Request

def get_user_id_from_req(req: Request):
    return req.state.user.get("id")