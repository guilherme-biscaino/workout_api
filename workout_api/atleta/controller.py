from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, status, Body, HTTPException
from pydantic import UUID4
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi_pagination import LimitOffsetPage, paginate

from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.categorias.models import CategoriaModel
from workout_api.atleta.models import AtletaModel
from workout_api.atleta.schemas import AtletaIn, AtletaOut, AtletaUpdate
from workout_api.contrib.dependencies import DataBaseDependency

router = APIRouter()


@router.post(
    path='/',
    summary="Criar novo atleta",
    status_code=status.HTTP_201_CREATED,
    response_model=AtletaOut

)
async def post(
        db_session: DataBaseDependency,
        atleta_in: AtletaIn = Body(...)) -> AtletaOut:

    nome_categoria = atleta_in.categoria.nome
    nome_centro_treinamento = atleta_in.centro_treinamento.nome

    categoria = (await db_session.execute(select(
        CategoriaModel).filter_by(nome=nome_categoria))).scalars().first()

    # pesquisa e valida se a categoria existe
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'A categoria: {nome_categoria}, não foi encontrada!'
        )

    # pesquisa e valida e so centro de treinamento existe
    centro_treinamento = (await db_session.execute(select(
        CentroTreinamentoModel).filter_by(nome=nome_centro_treinamento))).scalars().first()

    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'O centro de treinamento: {nome_centro_treinamento}, não foi encontrado!'
        )
    try:
        atleta_out: AtletaOut = AtletaOut(id=uuid4(), created_at=datetime.utcnow(), **atleta_in.model_dump())
        atleta_model = AtletaModel(**atleta_out.model_dump(exclude={'categoria', 'centro_treinamento'}))
        atleta_model.categoria_id = categoria.pk_id
        atleta_model.centro_treinamento_id = centro_treinamento.pk_id

        db_session.add(atleta_model)
        await db_session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail=f'Já existe um atleta cadastrado com o cpf: {atleta_in.cpf}',
        )

    except Exception as excecao:
         raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail=f"Occoreu um erro ao inserir os dados no banco {excecao}"
         )

    return atleta_out


@router.get(
    '/',
    summary='Consultar todos os Atletas',
    status_code=status.HTTP_200_OK,
    response_model=LimitOffsetPage[AtletaOut],
)
async def query(db_session: DataBaseDependency) -> LimitOffsetPage[AtletaOut]:
    atletas: list[AtletaOut] = (await db_session.execute(select(AtletaModel))).scalars().all()

    return paginate([AtletaOut.model_validate(atleta) for atleta in atletas])

try:
    @router.get(
        '/{id}',
        summary="Consulta atleta pelo id ou nome e cpf",
        status_code=status.HTTP_200_OK,
        response_model=AtletaOut
    )
    async def get(db_session: DataBaseDependency,
                  id: UUID4 = None,
                  nome: str = None,
                  cpf: str = None) -> AtletaOut:

        atleta: AtletaOut = (await db_session.execute(select(AtletaModel).filter_by(id=id))).scalars().first()

        # alteração feita para permitir que a busca seja feita pelo nome + cpf em caso do id não achar
        if not atleta:
            if nome and cpf:  # com certeza não é a melhor forma mas foi o que consegui pensar
                atleta: AtletaOut = (await db_session.execute(select(AtletaModel)
                                                              .filter_by(nome=nome, cpf=cpf))).scalars().first()
        if not atleta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nenhum atleta encontrado com o id: {id} ou nome: {nome} e cpf: {cpf}"
            )
        return atleta
except Exception as exceptional:
    print(exceptional)


@router.patch(
    '/{id}',
    summary="Altera informações do atleta pelo id",
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut
)
async def get(id: UUID4, db_session: DataBaseDependency, atlteta_up: AtletaUpdate) -> AtletaOut:
    atleta: AtletaOut = (await db_session.execute(select(AtletaModel).filter_by(id=id))).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhum atleta encontrado com o id: {id}"
        )
    atleta_up = atlteta_up.model_dump(exclude_unset=True)
    for key, value in atleta_up.items():
        setattr(atleta, key, value)
    await db_session.commit()
    await db_session.refresh(atleta)
    return atleta


@router.delete(
    '/{id}',
    summary="Deletar o atleta pelo id",
    status_code=status.HTTP_204_NO_CONTENT
)
async def get(id: UUID4, db_session: DataBaseDependency) -> None:
    atleta: AtletaOut = (await db_session.execute(select(AtletaModel).filter_by(id=id))).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhum atleta encontrado com o id: {id}"
        )
    await db_session.delete(atleta)
    await db_session.commit()
