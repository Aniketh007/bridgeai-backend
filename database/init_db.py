from prisma import Prisma
from typing import Optional

class db:

    def __init__(self):
        self.prisma = Prisma()

    async def connect(self):
        if self.prisma is None:
            self.prisma = Prisma()
        await self.prisma.connect()

    async def disconnect(self):
        if self.prisma is not None:
            await self.prisma.disconnect()
            self.prisma = None

    async def get_client(self) -> Optional[Prisma]:
        if self.prisma is None:
            await self.connect()
        return self.prisma

get_db = db()