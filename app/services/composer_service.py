from app.repositories.composer_repository import ComposerRepository

class ComposerService:
    def __init__(self, repository: ComposerRepository):
        self.repo = repository

    async def fetch_all_composers(self):
        # Aquí podrías añadir lógica de cache o filtrado adicional
        return await self.repo.get_composers_with_country()