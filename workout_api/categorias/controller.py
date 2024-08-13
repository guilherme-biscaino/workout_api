from uuid import uuid4

from fastapi import APIRouter, Body, status, HTTPException
from pydantic import UUID4
from sqlalchemy.future import select
from fastapi_pagination import LimitOffsetPage, paginate

from workout_api.categorias.schemas import CategoriaIn, CategoriaOut

from workout_api.contrib.dependencies import DataBaseDependency
from workout_api.categorias.models import CategoriaModel

router = APIRouter()


@router.post(
    '/',
    summary='Criar uma nova categoria',
    status_code=status.HTTP_201_CREATED,
    response_model=CategoriaOut,
)
async def post(
        db_session: DataBaseDependency,
        categoria_in: CategoriaIn = Body(...)
) -> CategoriaOut:
    categoria_out = CategoriaOut(id=uuid4(), **categoria_in.model_dump())
    categoria_model = CategoriaModel(**categoria_out.model_dump())

    db_session.add(categoria_model)
    await db_session.commit()

    return categoria_out
    pass


@router.get(
    '/',
    summary='consultar todas categorias',
    status_code=status.HTTP_200_OK,
    response_model=LimitOffsetPage[CategoriaOut],
)
async def query(
        db_session: DataBaseDependency,
) -> LimitOffsetPage[CategoriaOut]:
    categorias: list[CategoriaOut] = (await db_session.execute(select(CategoriaModel))).scalars().all()
    return paginate(categorias)


@router.get(
    '/{id}',
    summary='consultar categoria pelo id',
    status_code=status.HTTP_200_OK,
    response_model=CategoriaOut,
)
async def query(
        db_session: DataBaseDependency,
        id: UUID4
) -> CategoriaOut:
    categoria: CategoriaOut = (await db_session.execute(select(CategoriaModel).filter_by(id=id))
                               ).scalars().first()

    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Categoria não encontrada no id: {id}")
    return categoria
