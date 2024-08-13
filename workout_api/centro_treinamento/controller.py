from uuid import uuid4

from fastapi import APIRouter, Body, status, HTTPException
from fastapi_pagination import LimitOffsetPage, paginate
from pydantic import UUID4
from sqlalchemy.future import select
from workout_api.centro_treinamento.schemas import CentroTreinamentoIn, CentroTreinamentoOut

from workout_api.contrib.dependencies import DataBaseDependency
from workout_api.centro_treinamento.models import CentroTreinamentoModel

router = APIRouter()


@router.post(
    '/',
    summary='Criar um novo centro de treinamento',
    status_code=status.HTTP_201_CREATED,
    response_model=CentroTreinamentoOut,
)
async def post(
        db_session: DataBaseDependency,
        categoria_in: CentroTreinamentoIn = Body(...)
) -> CentroTreinamentoOut:
    centro_de_treinamento_out = CentroTreinamentoOut(id=uuid4(), **categoria_in.model_dump())
    centro_model = CentroTreinamentoModel(**centro_de_treinamento_out.model_dump())

    db_session.add(centro_model)
    await db_session.commit()

    return centro_de_treinamento_out


@router.get(
    '/',
    summary='consultar todos os centros de treinamento',
    status_code=status.HTTP_200_OK,
    response_model=LimitOffsetPage[CentroTreinamentoOut],
)
async def query(
        db_session: DataBaseDependency,
) -> LimitOffsetPage[CentroTreinamentoOut]:
    centro_treinamento: list[CentroTreinamentoOut] = (await db_session.execute(select(CentroTreinamentoModel))).scalars().all()
    return paginate(centro_treinamento)


@router.get(
    '/{id}',
    summary='consultar centro de treinamento pelo id',
    status_code=status.HTTP_200_OK,
    response_model=CentroTreinamentoOut,
)
async def query(
        db_session: DataBaseDependency,
        id: UUID4
) -> CentroTreinamentoOut:
    centro_treinamento: CentroTreinamentoOut = (await db_session.execute(select(CentroTreinamentoModel).filter_by(id=id))
                               ).scalars().first()

    if not centro_treinamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Centro de treinamento não encontrada no id: {id}")
    return centro_treinamento
