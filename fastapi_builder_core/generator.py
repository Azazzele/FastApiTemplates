import os
import traceback
from .models import EndpointModel
from .templates import ROUTER_TEMPLATE, SCHEMA_TEMPLATE, DB_MODEL_TEMPLATE, TEST_TEMPLATE, DOCKERFILE_TEMPLATE, DOCKER_COMPOSE_TEMPLATE

def create_project_structure(module: str, db_type: str) -> str:
    # 1. Жестко привязываем базовые пути к расположению папки app
    base_dir = os.path.join(os.getcwd(), "app")
    
    # 2. Находим корень целевого проекта (папка, где лежит app/)
    project_root = os.path.dirname(base_dir)
    
    module_dir = os.path.join(base_dir, module)
    tests_dir = os.path.join(project_root, "tests")
    
    for path in [base_dir, module_dir, tests_dir]:
        if not os.path.exists(path):
            os.makedirs(path)
            
    for path in [base_dir, module_dir]:
        init_file = os.path.join(path, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w", encoding="utf-8") as f:
                f.write("")
                
    # Формируем файл базы данных в зависимости от выбора
    db_file_path = os.path.join(base_dir, "database.py")
    if not os.path.exists(db_file_path):
        if db_type == "postgres":
            db_content = (
                "from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession\n"
                "from sqlalchemy.orm import declarative_base, sessionmaker\n"
                "import os\n\n"
                "DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5432/fastapi_db')\n\n"
                "engine = create_async_engine(DATABASE_URL, echo=True)\n"
                "SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)\n"
                "Base = declarative_base()\n\n"
                "async def get_db():\n"
                "    async with SessionLocal() as session:\n"
                "        try:\n"
                "            yield session\n"
                "        finally:\n"
                "            await session.close()\n"
            )
        else:
            db_content = (
                "from sqlalchemy import create_engine\n"
                "from sqlalchemy.ext.declarative import declarative_base\n"
                "from sqlalchemy.orm import sessionmaker\n\n"
                "SQLALCHEMY_DATABASE_URL = 'sqlite:///./sql_app.db'\n\n"
                "engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})\n"
                "SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)\n"
                "Base = declarative_base()\n\n"
                "def get_db():\n"
                "    db = SessionLocal()\n"
                "    try:\n"
                "        yield db\n"
                "    finally:\n"
                "        db.close()\n"
            )
        with open(db_file_path, "w", encoding="utf-8") as f:
            f.write(db_content)
            
    # Модуль авторизации JWT
    auth_file_path = os.path.join(base_dir, "auth.py")
    if not os.path.exists(auth_file_path):
        with open(auth_file_path, "w", encoding="utf-8") as f:
            f.write(
                "from fastapi import Depends, HTTPException, status\n"
                "from fastapi.security import OAuth2PasswordBearer\n"
                "from datetime import datetime, timedelta\n"
                "import jwt\n\n"
                "SECRET_KEY = 'SUPER_SECRET_KEY_DONT_STEAL'\n"
                "ALGORITHM = 'HS256'\n"
                "oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')\n\n"
                "def create_access_token(data: dict, expires_delta: timedelta = None):\n"
                "    to_encode = data.copy()\n"
                "    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))\n"
                "    to_encode.update({'exp': expire})\n"
                "    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)\n\n"
                "def get_current_user(token: str = Depends(oauth2_scheme)):\n"
                "    credentials_exception = HTTPException(\n"
                "        status_code=status.HTTP_401_UNAUTHORIZED,\n"
                "        detail='Could not validate credentials',\n"
                "        headers={'WWW-Authenticate': 'Bearer'},\n"
                "    )\n"
                "    try:\n"
                "        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])\n"
                "        username: str = payload.get('sub')\n"
                "        if username is None:\n"
                "            raise credentials_exception\n"
                "        return {'username': username}\n"
                "    except jwt.PyJWTError:\n"
                "        raise credentials_exception\n"
            )

    # 3. Запись Docker-файлов СТРОГО в project_root целевого проекта
    dockerfile_path = os.path.join(project_root, "Dockerfile")
    if not os.path.exists(dockerfile_path):
        with open(dockerfile_path, "w", encoding="utf-8") as f:
            f.write(DOCKERFILE_TEMPLATE)

    compose_path = os.path.join(project_root, "docker-compose.yml")
    if not os.path.exists(compose_path):
        with open(compose_path, "w", encoding="utf-8") as f:
            f.write(DOCKER_COMPOSE_TEMPLATE.render(db_type=db_type))

    # Настраиваем зависимости (для Postgres докидываем asyncpg)
    req_path = os.path.join(project_root, "requirements.txt")
    if not os.path.exists(req_path):
        libs = "fastapi>=0.100.0\nuvicorn>=0.22.0\nsqlalchemy>=2.0.0\npyjwt>=2.8.0\npytest>=7.4.0\nhttpx>=0.24.1\n"
        if db_type == "postgres":
            libs += "asyncpg>=0.28.0\ngreenlet>=3.0.0\n"
        with open(req_path, "w", encoding="utf-8") as f:
            f.write(libs)
            
    return module_dir


def rebuild_main_py(db_type: str):
    """Сканирует папку app и полностью пересобирает main.py со всеми найденными роутерами."""
    base_dir = os.path.join(os.getcwd(), "app")
    main_path = os.path.join(base_dir, "main.py")
    modules = []
    if os.path.exists(base_dir):
        for item in os.listdir(base_dir):
            if os.path.isdir(os.path.join(base_dir, item)) and os.path.exists(os.path.join(base_dir, item, "router.py")):
                modules.append(item)
    imports, includes = [], []
    for mod in modules:
        imports.append(f"from app.{mod}.router import router as {mod}_router")
        includes.append(f"app.include_router({mod}_router)")
    
    main_content = "from fastapi import FastAPI\n"
    if db_type == "sqlite":
        main_content += "from app.database import engine, Base\n"
        
    if imports: 
        main_content += "\n".join(imports) + "\n"
    
    if db_type == "sqlite":
        main_content += "\nBase.metadata.create_all(bind=engine)\n\n"
    else:
        main_content += "\n# Для производства с Postgres используйте миграции Alembic\n\n"
        
    main_content += "app = FastAPI(title='Сгенерированное FastAPI Приложение')\n\n"
    if includes: 
        main_content += "\n".join(includes) + "\n"
        
    with open(main_path, "w", encoding="utf-8") as f: 
        f.write(main_content)


def get_preview_code(data: EndpointModel) -> dict:
    clean_method = data.method.lower()
    clean_path = data.path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
    suffix = f"_{clean_path}" if clean_path else ""
    endpoint_name = f"{clean_method}_{data.module}{suffix}"
    request_model_name = f"{data.module.capitalize()}{clean_path.capitalize()}Request"
    response_model_name = f"{data.module.capitalize()}{clean_path.capitalize()}Response"
    module_model_name = data.module.capitalize()
    
    schema_content = ""
    if data.request_fields and data.method in ["POST", "PUT", "PATCH"]:
        schema_content += SCHEMA_TEMPLATE.render(model_name=request_model_name, fields=data.request_fields) + "\n"
    if data.response_fields:
        schema_content += SCHEMA_TEMPLATE.render(model_name=response_model_name, fields=data.response_fields) + "\n"
        
    has_body = bool(data.request_fields) and data.method in ["POST", "PUT", "PATCH"]
    router_content = ROUTER_TEMPLATE.render(
        module=data.module, method=data.method, path=data.path, summary=data.summary,
        endpoint_name=endpoint_name, has_body=has_body, request_model_name=request_model_name,
        response_model_name=response_model_name if data.response_fields else "dict",
        module_model_name=module_model_name, require_auth=data.require_auth
    )
    db_model_content = DB_MODEL_TEMPLATE.render(module_model_name=module_model_name, table_name=data.module, fields=data.request_fields)
    test_content = TEST_TEMPLATE.render(endpoint_name=endpoint_name, method=data.method, path=data.path, module=data.module, fields=data.request_fields, require_auth=data.require_auth)
    
    return {
        "router": router_content,
        "schemas": schema_content if schema_content else "# Схемы не требуются",
        "models": db_model_content,
        "tests": test_content
    }

def write_generated_code(data: EndpointModel):
    try:
        module_dir = create_project_structure(data.module)
        clean_method = data.method.lower()
        clean_path = data.path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
        suffix = f"_{clean_path}" if clean_path else ""
        endpoint_name = f"{clean_method}_{data.module}{suffix}"
        request_model_name = f"{data.module.capitalize()}{clean_path.capitalize()}Request"
        response_model_name = f"{data.module.capitalize()}{clean_path.capitalize()}Response"
        module_model_name = data.module.capitalize()
        
        # 1. Схемы
        schemas_path = os.path.join(module_dir, "schemas.py")
        schema_content = ""
        if data.request_fields and data.method in ["POST", "PUT", "PATCH"]:
            schema_content += SCHEMA_TEMPLATE.render(model_name=request_model_name, fields=data.request_fields) + "\n"
        if data.response_fields:
            schema_content += SCHEMA_TEMPLATE.render(model_name=response_model_name, fields=data.response_fields) + "\n"
        with open(schemas_path, "a" if os.path.exists(schemas_path) else "w", encoding="utf-8") as f: f.write(schema_content)
            
        # 2. Модели БД
        models_path = os.path.join(module_dir, "models.py")
        if not os.path.exists(models_path):
            with open(models_path, "w", encoding="utf-8") as f:
                f.write(DB_MODEL_TEMPLATE.render(module_model_name=module_model_name, table_name=data.module, fields=data.request_fields))
            
        # 3. Роутер
        router_path = os.path.join(module_dir, "router.py")
        has_body = bool(data.request_fields) and data.method in ["POST", "PUT", "PATCH"]
        router_content = ROUTER_TEMPLATE.render(
            module=data.module, method=data.method, path=data.path, summary=data.summary,
            endpoint_name=endpoint_name, has_body=has_body, request_model_name=request_model_name,
            response_model_name=response_model_name if data.response_fields else "dict",
            module_model_name=module_model_name, require_auth=data.require_auth
        )
        if os.path.exists(router_path):
            lines = router_content.split("\n")[5:]
            router_content = "\n" + "\n".join(lines)
        with open(router_path, "a" if os.path.exists(router_path) else "w", encoding="utf-8") as f: f.write(router_content)
            
        # 4. Запись тестов
        if data.generate_tests:
            base_dir = os.path.join(os.getcwd(), "app")
            project_root = os.path.dirname(base_dir)
            tests_dir = os.path.join(project_root, "tests")
            
            test_file_path = os.path.join(tests_dir, f"test_{data.module}.py")
            test_content = TEST_TEMPLATE.render(
                endpoint_name=endpoint_name, 
                method=data.method, 
                path=data.path, 
                module=data.module, 
                fields=data.request_fields, 
                require_auth=data.require_auth
            )
            with open(test_file_path, "a" if os.path.exists(test_file_path) else "w", encoding="utf-8") as f:
                f.write("\n" + test_content)
                
        rebuild_main_py()
    except Exception as e:
        print("💥 ОШИБКА ГЕНЕРАЦИИ КОДА:")
        traceback.print_exc()
        raise e


def write_generated_code(data: EndpointModel):
    try:
        module_dir = create_project_structure(data.module, data.db_type)
        clean_method = data.method.lower()
        clean_path = data.path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
        suffix = f"_{clean_path}" if clean_path else ""
        endpoint_name = f"{clean_method}_{data.module}{suffix}"
        request_model_name = f"{data.module.capitalize()}{clean_path.capitalize()}Request"
        response_model_name = f"{data.module.capitalize()}{clean_path.capitalize()}Response"
        module_model_name = data.module.capitalize()
        
        # 1. Запись schemas.py
        schemas_path = os.path.join(module_dir, "schemas.py")
        schema_content = ""
        if data.request_fields and data.method in ["POST", "PUT", "PATCH"]:
            schema_content += SCHEMA_TEMPLATE.render(model_name=request_model_name, fields=data.request_fields) + "\n"
        if data.response_fields:
            schema_content += SCHEMA_TEMPLATE.render(model_name=response_model_name, fields=data.response_fields) + "\n"
        with open(schemas_path, "a" if os.path.exists(schemas_path) else "w", encoding="utf-8") as f:
            f.write(schema_content)
            
        # 2. Запись models.py
        models_path = os.path.join(module_dir, "models.py")
        if not os.path.exists(models_path):
            with open(models_path, "w", encoding="utf-8") as f:
                f.write(DB_MODEL_TEMPLATE.render(module_model_name=module_model_name, table_name=data.module, fields=data.request_fields))
            
        # 3. Запись router.py
        router_path = os.path.join(module_dir, "router.py")
        has_body = bool(data.request_fields) and data.method in ["POST", "PUT", "PATCH"]
        router_content = ROUTER_TEMPLATE.render(
            module=data.module, method=data.method, path=data.path, summary=data.summary,
            endpoint_name=endpoint_name, has_body=has_body, request_model_name=request_model_name,
            response_model_name=response_model_name if data.response_fields else "dict",
            module_model_name=module_model_name, require_auth=data.require_auth, db_type=data.db_type
        )
        if os.path.exists(router_path):
            lines = router_content.split("\n")[6:]
            router_content = "\n" + "\n".join(lines)
        with open(router_path, "a" if os.path.exists(router_path) else "w", encoding="utf-8") as f:
            f.write(router_content)
            
        # 4. Запись тестов
        if data.generate_tests:
            base_dir = os.path.join(os.getcwd(), "app")
            project_root = os.path.dirname(base_dir)
            tests_dir = os.path.join(project_root, "tests")
            test_file_path = os.path.join(tests_dir, f"test_{data.module}.py")
            test_content = TEST_TEMPLATE.render(
                endpoint_name=endpoint_name, 
                method=data.method, 
                path=data.path, 
                module=data.module, 
                fields=data.request_fields, 
                require_auth=data.require_auth
            )
            with open(test_file_path, "a" if os.path.exists(test_file_path) else "w", encoding="utf-8") as f:
                f.write("\n" + test_content)
                
        rebuild_main_py(data.db_type)
    except Exception as e:
        print("💥 ОШИБКА ГЕНЕРАЦИИ КОДА:")
        traceback.print_exc()
        raise e
