import os
import requests
from pandas import DataFrame
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()


class GSEClient:

    def __init__(self):

        self.protocol = os.getenv("GSE_PROTOCOL")
        self.host = os.getenv("GSE_HOST")

        self.client_id = os.getenv("GSE_CLIENT_ID")
        self.client_secret = os.getenv("GSE_CLIENT_SECRET")

        self.base_url = f"{self.protocol}://{self.host}/api/v1"

        self.access_token = None
        self.expires_at = None


    # ---------------------------------------------------
    # STATUS
    # ---------------------------------------------------
    def status(self):

        url = f"{self.base_url}/status"

        r = requests.get(
            url,
            headers={"Accept": "application/json"}
        )

        r.raise_for_status()

        return r.json()


    # ---------------------------------------------------
    # TOKEN
    # ---------------------------------------------------
    def get_token(self):

        url = f"{self.base_url}/auth/token"

        payload = {
            "clientId": self.client_id,
            "clientSecret": self.client_secret
        }

        r = requests.post(
            url,
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )

        r.raise_for_status()

        data = r.json()

        self.access_token = data["accessToken"]

        self.expires_at = datetime.fromisoformat(
            data["expiresAt"].replace("Z", "+00:00")
        )
        
        return data


    # ---------------------------------------------------
    # TOKEN VALIDO
    # ---------------------------------------------------
    def ensure_token(self):

        if self.access_token is None:
            self.get_token()
            return

        now = datetime.now(timezone.utc)

        if now >= self.expires_at:
            self.get_token()


    # ---------------------------------------------------
    # HVAC
    # ---------------------------------------------------
    def hvac_valores(
        self,
        id_cliente: int,
        fec_ini: str,
        fec_fin: str,
        id_region: int
    ):

        self.ensure_token()

        url = f"{self.base_url}/hvac/valores"

        params = {
            "idCliente": id_cliente,
            "fecIni": fec_ini,
            "fecFin": fec_fin,
            "idRegion": id_region
        }

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        r = requests.get(
            url,
            headers=headers,
            params=params
        )

        r.raise_for_status()
        
        return r.json()
    
    def clientes_regiones(self):
        self.ensure_token()

        url = f"{self.base_url}/clientes/regiones"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
        try:
            r = requests.get(url, headers=headers)
            r.raise_for_status()

            data = r.json()

            data = data[0]

            return data
        except Exception as e: 
            print(f"Error API: {e} - {datetime.now().strftime('%H:%M:%S')}")
            return []