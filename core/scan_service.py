import json
import subprocess
from typing import Dict, Any
from database.init_db import get_db
from schemas.scan import ScanResponse
from prisma import Prisma


class ScanService:
    """
    Service class for handling scan-related operations.
    """

    async def create_scan(self, user_id: str, url: str):
        """
        Save a new scan to the table
        """
        prisma = await get_db.get_client()
        new_scan = await prisma.scan.create(
            data={
                "userId": user_id,
                "url": url,
                "status": "pending"
            }
        )
        return new_scan.id

    async def get_scan_by_id(self, scan_id: str):
        """
        Get a scan by its ID
        """
        prisma = await get_db.get_client()
        scan = await prisma.scan.find_unique(
            where={"id": scan_id},
            include={"user": True}
        )
        return scan

    async def get_scans_by_user(self, user_id: str):
        """
        Get all scans for a specific user
        """
        prisma = await get_db.get_client()
        scans = await prisma.scan.find_many(
            where={"userId": user_id},
            order=[{"createdAt": "desc"}],
        )
        return scans

    async def update_scan_result(self, scan_id: str, result: Dict[str, Any], status: str = "completed"):
        """
        Update scan result and status after processing.
        """
        prisma = await get_db.get_client()
        scan = await prisma.scan.update(
            where={
                "id": scan_id
            },
            data={
                "result": json.dumps(result),  # JSON field
                "status": status
            }
        )
        return scan

    async def update_scan_from_task(self, scan_id: str, result: Dict[str, Any], status: str):
        """
        Connects, updates, and disconnects. For use in background tasks.
        """
        prisma = Prisma(log_queries=False)
        try:
            await prisma.connect()
            
            await prisma.scan.update(
                where={"id": scan_id},
                # FIX: Also ensure the result is converted to a JSON string.
                data={"result": json.dumps(result), "status": status}
            )
        finally:
            if prisma.is_connected():
                await prisma.disconnect()

scan_service = ScanService()