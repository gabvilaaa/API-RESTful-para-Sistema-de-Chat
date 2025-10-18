# API RESTful para Sistema de Chat
Grupo: Helder Thadeu e Gabriel Vieira

# Descrição

Um sistema de chat em tempo real desenvolvido com FastAPI, que suporta gerenciamento de usuários, salas e mensagens, com autenticação JWT, permissões e WebSockets para comunicação em tempo real.

# Estrutura do Projeto
1. main.py              # Programa principal utilizando FastAPI

2. identities.py        # Classes utilizadas (Users, rooms e messages)

3. database.py          # Configuração do banco de dados PostgreSQL

4. auth.py              # Configuração do sistema de autenticação JWT

5. static/              # Pasta onde os arquivos de teste e resultados são salvos

        chat.html      # Menu principal do chat utilizando HTML + CSS + JS
        
        index.html     # Página de login
    
6. README.md

# Funcionalidades

CRUD de usuários e salas de chat

Autenticação de usuários via JWT

Controle de permissões por usuário e sala

Envio e recebimento de mensagens em tempo real via WebSockets

Persistência de dados com PostgreSQL

Documentação automática de API com Swagger

Estrutura modular para fácil manutenção e expansão

# Tecnologias
* Python 3.8+

* FastAPI

* PostgreSQL (banco de dados)

# Como Compilar e Executar
Instale o python e as bibliotecas fastAPI(principal) e as auxiliares;
No terminal, dentro da pasta do projeto, execute: uvicorn app:main --reload
Abra seu navegador na porta mencionada no terminal
