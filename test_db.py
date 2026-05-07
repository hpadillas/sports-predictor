from app.database import engine
from app.models import metadata

metadata.create_all(engine)

print("Base de datos conectada y tabla creada")