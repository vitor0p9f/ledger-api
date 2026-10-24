import strawberry
from strawberry.fastapi import GraphQLRouter

@strawberry.type
class HealthResponse:
    message: str


@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> HealthResponse:
        return HealthResponse(message="API is healthy and running!")


schema = strawberry.Schema(Query)

graphQL_router = GraphQLRouter(schema)