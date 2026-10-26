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

health_schema = strawberry.Schema(Query)
graphql_health_router = GraphQLRouter(health_schema)
