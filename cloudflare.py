from datetime import datetime
import hashlib
import os
import requests
import hmac

class CloudFlareImages():
    # https://api.cloudflare.com/#getting-started-requests
    ENDPOINT_BASE = "https://api.cloudflare.com/client/v4"

    # https://developers.cloudflare.com/images/cloudflare-images/upload-images/formats-limitations
    SUPPORTED_FORMATS = [".png", ".gif", ".jpeg", ".jpg", ".webp", ".svg"]
    MAX_WIDTH = 10000
    MAX_HEIGHT = 10000
    MAX_SIZE_MB = 10
    
    def __init__(self, apiKey: str, accountId: str, email: str, accountHash: str) -> None:
        # Credentials
        self.apiKey = apiKey
        self.accountId = accountId
        self.email = email
        self.accountHash= accountHash

        self.requestHeaders = {
            "X-Auth-Key": self.apiKey,
            "X-Auth-Email": self.email
        }
        
        # Endpoints
        self.authenticatedUploadURL = f"accounts/{self.accountId}/images/v2/direct_upload"

    def _checkIfImageSupported(self, path: str) -> bool:
        file_extension = os.path.splitext(path)[1].lower()
        return file_extension in self.SUPPORTED_FORMATS

    def listImages(self, page: int=1, perPage: int=50) -> dict:
        # https://api.cloudflare.com/#cloudflare-images-list-images

        endpoint = f"{self.ENDPOINT_BASE}/accounts/{self.accountId}/images/v1"

        return requests.get(
            endpoint,
            headers = self.requestHeaders,
        ).json()

    def createDirectUploadLink(self, requireSignedURLs: bool=False, metaData: dict=None, expiry: datetime=None) -> dict:
        # https://api.cloudflare.com/#cloudflare-images-create-authenticated-direct-upload-url-v2

        endpoint = f"{self.ENDPOINT_BASE}/accounts/{self.accountId}/images/v2/direct_upload"
        payload = {}
        
        payload["requireSignedURLs"] = requireSignedURLs
        if metaData != None:
            payload["metadata"] = metaData
        if expiry != None:
            payload["expiry"] = expiry

        return requests.post(
            endpoint,
            headers = self.requestHeaders,
            params = payload
            ).json()

    def upload(self, directUploadResponse: dict, imagePath: str) -> dict:
        # https://developers.cloudflare.com/images/cloudflare-images/upload-images/direct-creator-upload/

        file = {"file": open(imagePath, "rb")}

        return requests.post(
            directUploadResponse["result"]["uploadURL"],
            headers = self.requestHeaders,
            files = file
        ).text

    def listVariants(self) -> dict:
        # https://api.cloudflare.com/#cloudflare-images-variants-update-a-variant
        return requests.get(
            f"{self.ENDPOINT_BASE}/accounts/{self.accountId}/images/v1/variants",
            headers = self.requestHeaders
        ).json()

    def createVariant(self, name: str, fitType: str, width: int, height: int, metaDataToSave: str="none", neverRequireSignedURLs: bool=False) -> dict:
        # https://api.cloudflare.com/#cloudflare-images-variants-create-a-variant

        """
        
        metaDataToSave: "none", "keep" or "copyright"
        fit: "scale-down", "contain", "cover", "crop" or "pad"
        
        """

        payload = {
            "id": name,
            "options": {
                "fit": fitType,
                "metadata": metaDataToSave,
                "width": width,
                "height": height
            },
            "neverRequireSignedURLs": neverRequireSignedURLs
        }

        return requests.post(
            f"{self.ENDPOINT_BASE}/accounts/{self.accountId}/images/v1/variants",
            headers = self.requestHeaders,
            json = payload
        ).json()

    def deleteImage(self, id: str) -> dict:
        # https://api.cloudflare.com/#cloudflare-images-delete-image
        return requests.delete(
            f"{self.ENDPOINT_BASE}/accounts/{self.accountId}/images/v1/{id}",
            headers = self.requestHeaders
            ).json()

    def getVariantDetails(self, name: str) -> dict:
        # https://api.cloudflare.com/#cloudflare-images-variants-variant-details
        return requests.get(
            f"{self.ENDPOINT_BASE}/accounts/{self.accountId}/images/v1/variants/{name}",
            headers = self.requestHeaders
        ).json()

    def updateVariant(self, name: str, fitType: str, width: int, height: int, metaDataToSave: str) -> dict:
        # https://api.cloudflare.com/#cloudflare-images-variants-update-a-variant

        details = self.getVariantDetails(name)["result"][name]["options"]

        return requests.post(
            f"{self.ENDPOINT_BASE}/accounts/{self.accountId}/images/v1/variants/{name}",
            headers = self.requestHeaders,
            json = {
                "fit": fitType if details["fit"] != fitType else details["fit"],
                "metadata": metaDataToSave if details["metadata"] != metaDataToSave else details["metadata"],
                "width": width if details["width"] != width else details["width"],
                "height": width if details["height"] != height else details["height"]
            }
        ).json()

    def deleteVariant(self, name: str) -> dict:
        # https://api.cloudflare.com/#cloudflare-images-variants-delete-a-variant
        return requests.delete(
            f"{self.ENDPOINT_BASE}/accounts/{self.accountId}/images/v1/variants/{name}",
            headers = self.requestHeaders
            ).json()

    def getImageDetails(self, id: str) -> dict:
        # https://api.cloudflare.com/#cloudflare-images-image-details
        return requests.get(
            f"{self.ENDPOINT_BASE}/accounts/{self.accountId}/images/v1/{id}",
            headers = self.requestHeaders
        ).json()

    def getCustomizedURL(self, domain: str, imageId: str, variant: str) -> str:
        # https://developers.cloudflare.com/images/cloudflare-images/serve-images/serve-images-custom-domains/
        domain = domain.lower()

        if domain.startswith("http://"):
            domain = domain.replace("http://", "https://")
        elif not domain.startswith("https://"):
            domain = "https://" + domain

        return f"{domain}/cdn-cgi/imagedelivery/{self.accountHash}/{imageId}/{variant}"