from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime
from fastapi import FastAPI, Depends,WebSocket, WebSocketDisconnect
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from database import get_db
from identities import User, UserCreate, Room, RoomCreate, RoomMembers, MessageCreate, Message, UserAuth


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

connections = {}

@app.websocket("/ws/{room_id}/{username}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, username: str):
    await websocket.accept()
    if room_id not in connections:
        connections[room_id] = []
    connections[room_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            for conn in connections[room_id]:
                await conn.send_json({"sender": username, "content": data["content"]})
    except WebSocketDisconnect:
        connections[room_id].remove(websocket)

@app.get("/")
def root():
    return FileResponse("static/index.html")

#------------------USERS--------------------------------------
@app.post("/users")
def createUser(user:UserCreate ,db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
            (User.email == user.email) | (User.username == user.username)
        ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email ou username já cadastrado")
    
    db_user = User(
        name=user.name,
        username=user.username,
        email=user.email,
        password=user.password, # salva senha em hash
        role='user'
    )

    db.add(db_user)
    db.commit()
    return {"message": f"Usuário {db_user.username} criado com sucesso!"}

@app.post("/users/login")
def user_auth(user: UserAuth ,db: Session = Depends(get_db)):
    check_user = check_user = db.query(User).filter(
        or_(
            User.username == user.emailUsername,
            User.email == user.emailUsername
        ),
        User.password == user.password
    ).first()
    if not check_user:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
    
    return {"message": f"Usuário {user.emailUsername} autenticado com sucesso"} 
      
@app.get("/Allusers")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@app.get("/users/{userId}")
def getUser(userId:int, db:Session = Depends(get_db)):
    user = db.query(User).filter((User.id == userId)).first()
    if not user:
        return {"error": "Usuário não encontrado"}
    return user

#------------------ROOMS--------------------------------------
@app.post("/rooms")
def createRoom(room : RoomCreate, db:Session = Depends(get_db)):
    existing_room = db.query(Room).filter(
            (Room.name == room.name)
        ).first()
    if existing_room:
        raise HTTPException(status_code=400, detail="Sala já cadastrada")
    
    db_room = Room(
        name=room.name,
        description=room.description,
        members = room.members,
        is_private = room.is_private
    )

    db.add(db_room)
    db.commit()
    db.refresh(db_room)  # retorna o objeto atualizado com ID
    return db_room

@app.delete("/rooms/{roomId}")
def func():
    output = " Remove uma sala (apenas pelo dono ou administrador)."
    return output

@app.post("/rooms/{roomId}/enter")
def joinRoom(roomId:int, userId:int, db:Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == roomId).first()
    user = db.query(User).filter(User.id == userId).first()
    members = db.query(RoomMembers).filter(RoomMembers.room_id == roomId ,RoomMembers.user_id == userId).first()

    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if members:
        raise HTTPException(status_code=400, detail="Usuário já está na sala")
    
    db_members = RoomMembers(
        user_id = userId,
        room_id = roomId
    )

    db.add(db_members)
    db.commit()
    db.refresh(db_members)  # retorna o objeto atualizado com ID
    return db_members
    

@app.post("/rooms/{roomId}/leave")
def leaveRoom(roomId:int, userId:int, db:Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == roomId).first()
    user = db.query(User).filter(User.id == userId).first()
    members = db.query(RoomMembers).filter(RoomMembers.room_id == roomId  ,RoomMembers.user_id == userId).first()

    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if not members:
        raise HTTPException(status_code=400, detail="Usuário não faz parte desta sala")
    
    db.delete(members)
    db.commit()

    return {"message": f"Usuário {userId} saiu da sala {roomId}"}


# Adm está se removendo aqui. Precisa implementar a validação JWT/OAuth antes dessa parte
@app.delete("/rooms/{roomId}/users/{userId}")
def adminRemove(roomId:int, userId:int,db:Session = Depends(get_db)):
    user = db.query(User).filter(User.id == userId, User.role == 'admin').first()
    room = db.query(Room).filter(Room.id == roomId).first()
    members = db.query(RoomMembers).filter(RoomMembers.room_id == roomId ,RoomMembers.user_id == userId).first()

    if not user: 
        raise HTTPException(status_code=404, detail='Você não pode executar esta ação pois não é administrador')
    
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")

    if not members:
        raise HTTPException(status_code=400, detail="Usuário não faz parte desta sala")
    
    db.delete(members)
    db.commit()
    
    return {"message": f"Usuário {userId} foi removido da sala {roomId}"}

@app.get("/rooms")
def get_rooms(db:Session = Depends(get_db) ):
    room = db.query(Room).first()
    return room

#----------------MESSAGES-----------------------------------
@app.post("/messages/direct/{receiverId}")
def direct(senderId: int, receiverId: int, content: str, db: Session = Depends(get_db)):
    # Verifica se o destinatário existe
    receiver = db.query(User).filter(User.id == receiverId).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Usuário destinatário não encontrado")

    # Busca salas em que o remetente participa
    sender_rooms = db.query(RoomMembers.room_id).filter(RoomMembers.user_id == senderId).all()

    # Busca salas em que o destinatário participa
    receiver_rooms = db.query(RoomMembers.room_id).filter(RoomMembers.user_id == receiverId).all()

    # Extrai apenas os IDs das salas
    s_rooms = [s.room_id for s in sender_rooms]
    r_rooms = [r.room_id for r in receiver_rooms]

    # Interseção — salas em comum
    comum = list(set(s_rooms) & set(r_rooms))

    if not comum:
        raise HTTPException(status_code=400, detail="Usuários não compartilham nenhuma sala")

    # Agora verifica se há pelo menos uma sala privada entre eles
    private_room = db.query(Room).filter(
        Room.id.in_(comum),
        Room.is_private == True
    ).first()

    if not private_room:
        raise HTTPException(status_code=403, detail="Nenhuma sala privada encontrada entre os usuários")

    # Cria a mensagem
    now = datetime.now()
    message = Message(
        room_id=private_room.id,
        sender_id=senderId,
        receiver_id=receiverId,
        content=content,
        created_at=now
    )

    db.add(message)
    db.commit()

    return {
        "message": f"Mensagem '{content}' enviada de {senderId} para {receiverId}",
        "room_id": private_room.id
    }

@app.post("/rooms/{roomId}/messages")
def groupMessage(senderId: int, roomId: int, content: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == roomId).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")

    membership = db.query(RoomMembers).filter(
        RoomMembers.room_id == roomId,
        RoomMembers.user_id == senderId
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Usuário não faz parte desta sala")

    # 3️⃣ Criar mensagem
    message = Message(
        room_id=roomId,
        sender_id=senderId,
        receiver_id = None,
        content=content,
        created_at=datetime.now()
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return {"message": f"Mensagem enviada para sala {roomId}", "message_id": message.id}

    
@app.get("/rooms/{roomId}/messages")
def getMessages(roomId:int,db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.room_id == roomId).all()

    return messages




