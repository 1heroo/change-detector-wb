from source.core.base_utils import BaseUtils
from source.core.settings import settings


class AdvertisementApiUtils(BaseUtils):

    async def send_detected_changes(self, detected_changes):
        url = settings.ADVERTISEMENT_PROJECT_HOST + '/api/v1/external-api/save-stats-to-detected-changes/'
        payload_changes = []
        for change in detected_changes:
            payload_changes.append({
                'nm_id': change.nm_id,
                'action': change.action,
                'shop_id': 1,
                'time': str(change.created_at)
            })
        await self.make_post_request(url=url, payload=dict(data=payload_changes), headers={}, no_json=True)
