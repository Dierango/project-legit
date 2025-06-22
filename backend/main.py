# main.py
import os
import subprocess
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv # .env dosyasını yüklemek için

# .env dosyasını yükle - Uygulama başladığında ortam değişkenleri buradan okunacak
load_dotenv()

# FastAPI uygulamasını başlat
app = FastAPI()

# --- Model Tanımlamaları ---
# Ürün kaydı için istek modeli
class RegisterProductRequest(BaseModel):
    product_id: str
    # Not: Akıllı sözleşmedeki register_product fonksiyonu şu an Product struct'ı içinde model, serial_number, production_date gibi alanları içermiyor.
    # Eğer akıllı sözleşmeye eklersen, bu model ve ilgili endpoint'i de güncellemen gerekir.

# Ürün detaylarını almak için yanıt modeli
class ProductDetails(BaseModel):
    product_id: str
    manufacturer: str
    current_owner: str
    registered_at: int
    # Not: Akıllı sözleşmedeki Product struct'ı içinde model, serial_number, production_date gibi alanlar şu an mevcut değil.
    # Eğer akıllı sözleşmeye eklersen, bu modeli de güncellemen gerekir.

# Ürün sahipliği transferi için istek modeli
class TransferProductRequest(BaseModel):
    product_id: str
    current_owner_public_key: str # Transferi başlatan kişinin public key'i (imzalayan kişi)
    new_owner_public_key: str # Ürünün yeni sahibinin public key'i

# --- Yardımcı Fonksiyon: Soroban CLI Komutlarını Çalıştırma ---
def run_soroban_command(command: list[str]):
    """Soroban CLI komutunu çalıştırır ve çıktıyı döndürür."""
    print(f"Executing command: {' '.join(command)}") # Komutu logla
    try:
        # Komutu çalıştırma ve çıktıyı yakalama
        result = subprocess.run(
            command,
            capture_output=True,
            text=True, # Metin çıktısı almak için
            check=True # Hata durumunda istisna fırlatır
        )
        print(f"Command stdout: {result.stdout}") # Stdout'u logla
        print(f"Command stderr: {result.stderr}") # Stderr'ı logla
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Hata durumunda stderr'ı döndür
        print(f"Komut Hatası: {e.cmd}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"Soroban CLI Hatası: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Beklenmeyen Hata: {str(e)}")

# --- API Endpoint'leri ---

@app.get("/")
async def read_root():
    """Ana dizin için karşılama mesajı."""
    return {"message": "Welcome to Product Authenticity Backend API"}

@app.post("/register_product")
async def register_product_api(request: RegisterProductRequest):
    """
    Yeni bir ürünü akıllı sözleşme üzerinde kaydeder.
    Sözleşme çağrısını Alice hesabı ile yapar ve Alice üretici olarak kaydedilir.
    """
    # Kontrat ID ve Alice'in Public Key'ini ortam değişkenlerinden al
    CONTRACT_ID = os.getenv("SOROBAN_CONTRACT_ID")
    ALICE_PUBLIC_KEY = os.getenv("ALICE_PUBLIC_KEY")

    if not CONTRACT_ID or not ALICE_PUBLIC_KEY:
        raise HTTPException(status_code=500, detail="SOROBAN_CONTRACT_ID or ALICE_PUBLIC_KEY environment variables not set. Please check your .env file.")

    # Soroban CLI komutunu oluşturma
    # Akıllı sözleşmedeki register_product fonksiyonunun signature'ı:
    # `register_product(env: Env, manufacturer: Address, product_id: String)`
    # olduğu için manufacturer parametresini de göndermemiz gerekiyor.
    command = [
        "soroban", "contract", "invoke",
        "--id", CONTRACT_ID,
        "--source", "alice", # Alice'in identity alias'ı (cli config'de tanımlı olmalı)
        "--network", "testnet",
        "--",
        "register_product",
        "--manufacturer", ALICE_PUBLIC_KEY, # Akıllı sözleşme bu parametreyi bekliyor
        "--product_id", request.product_id
    ]

    try:
        # Komutu çalıştırma
        output = run_soroban_command(command)
        return {"status": "success", "message": "Product registration initiated", "cli_output": output}
    except HTTPException as e:
        raise e

@app.post("/transfer_ownership")
async def transfer_ownership_api(request: TransferProductRequest):
    """
    Akıllı sözleşme üzerinde bir ürünün sahipliğini transfer eder.
    NOT: Akıllı sözleşmedeki transfer_ownership fonksiyonu,
    işlemi çağıranın (source) 'current_owner' olmasını bekler ve ondan yetki (require_auth) ister.
    Bu backend'de basitlik adına, her transferin 'alice' hesabı üzerinden yapıldığı varsayılıyor.
    Yani, product'ın current_owner'ı 'alice' olmalı veya 'alice' bu transferi yapma yetkisine sahip olmalı.
    Gerçek bir uygulamada, 'current_owner'ın kendi cüzdanıyla işlemi imzalaması gerekir.
    """
    CONTRACT_ID = os.getenv("SOROBAN_CONTRACT_ID")
    ALICE_PUBLIC_KEY = os.getenv("ALICE_PUBLIC_KEY") # Sadece test amaçlı, imzalayanın alice olduğu varsayılıyor

    if not CONTRACT_ID or not ALICE_PUBLIC_KEY:
        raise HTTPException(status_code=500, detail="SOROBAN_CONTRACT_ID or ALICE_PUBLIC_KEY environment variables not set. Please check your .env file.")

    # Akıllı sözleşmedeki transfer_ownership fonksiyonunun signature'ı:
    # `transfer_ownership(env: Env, current_owner: Address, product_id: String, new_owner: Address)`
    command = [
        "soroban", "contract", "invoke",
        "--id", CONTRACT_ID,
        "--source", "alice", # Bu işlem alice tarafından imzalanıyor
        "--network", "testnet",
        "--",
        "transfer_ownership",
        "--current_owner", request.current_owner_public_key, # Akıllı sözleşme bu parametreyi bekliyor
        "--product_id", request.product_id,
        "--new_owner", request.new_owner_public_key
    ]

    try:
        output = run_soroban_command(command)
        return {"status": "success", "message": "Ownership transfer initiated", "cli_output": output}
    except HTTPException as e:
        raise e


@app.get("/get_product_details/{product_id}")
async def get_product_details_api(product_id: str):
    """
    Akıllı sözleşme üzerinden ürün detaylarını alır.
    """
    CONTRACT_ID = os.getenv("SOROBAN_CONTRACT_ID")
    if not CONTRACT_ID:
        raise HTTPException(status_code=500, detail="SOROBAN_CONTRACT_ID environment variable not set. Please check your .env file.")

    command = [
        "soroban", "contract", "invoke",
        "--id", CONTRACT_ID,
        "--source", "alice", # Sadece okuma işlemi olduğu için herhangi bir hesaptan çağırabiliriz (örneğin alice)
        "--network", "testnet",
        "--",
        "get_product_details",
        "--product_id", product_id
    ]

    try:
        output = run_soroban_command(command)
        # Soroban CLI'dan gelen çıktının JSON olduğunu varsayıyoruz
        # Output bir string olarak geliyor, onu JSON'a parse etmemiz gerekiyor.
        # CLI çıktısı bazen ek metin (örn. INFO logları) içerebilir, bu yüzden sadece JSON kısmını ayıklamamız gerekebilir.
        json_start = output.find('{')
        json_end = output.rfind('}') + 1
        
        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_str = output[json_start:json_end]
            product_data = json.loads(json_str)
            return ProductDetails(**product_data)
        else:
            raise HTTPException(status_code=500, detail=f"Failed to parse product details from CLI output. Raw output: {output}")
    except HTTPException as e:
        raise e
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Invalid JSON output from Soroban CLI: {output}")

# --- Ek Bilgiler ---
# Bu API'yi çalıştırmak için:
# 1. `backend` dizinine gidin
# 2. Sanal ortamı etkinleştirin (`source venv/bin/activate`)
# 3. `backend/.env` dosyası oluşturun ve içine şu satırları ekleyin (kendi değerlerinizle):
#    SOROBAN_CONTRACT_ID="CBLMXIIBXAQKWEOXKYAQ5MMXELRTGJEHGSEU2VTR3GUTESNVGK3FPKX5"
#    ALICE_PUBLIC_KEY="GD23ZFKW4QLVX3TMDXE45RSUDGKJ6EL6TCXSE7RTMJEXKFS5INE7PSJ3"
# 4. `uvicorn main:app --reload` komutunu çalıştırın
#
# API, genellikle http://127.0.0.1:8000 adresinde çalışacaktır.
# Otomatik API dokümantasyonu için http://127.0.0.1:8000/docs adresini ziyaret edin.
