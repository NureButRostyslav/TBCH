import requests
import os
from getpass import getpass
from PIL import Image
import shutil

SERVER = "http://127.0.0.1:5000"
DOWNLOAD_FOLDER = "client_downloads"
if os.path.exists(DOWNLOAD_FOLDER):
    shutil.rmtree(DOWNLOAD_FOLDER)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

token = None
username = None

def api_post(path, json_data=None, files=None, headers=None, data=None):
    url = SERVER + path
    hd = headers or {}
    if token:
        hd["X-Token"] = token
    r = requests.post(url, json=json_data, files=files, headers=hd, data=data)
    try:
        return r.status_code, r.json()
    except:
        return r.status_code, {"raw": r.text}

def api_get(path, params=None):
    url = SERVER + path
    hd = {}
    if token:
        hd["X-Token"] = token
    r = requests.get(url, params=params, headers=hd)
    try:
        return r.status_code, r.json()
    except:
        return r.status_code, {"raw": r.text}

def register():
    global username
    user = input("username: ")
    pw = getpass("password: ")
    sc, res = api_post("/register", json_data={"username": user, "password": pw})
    print(sc, res)
    if sc == 200:
        print("Registered. Now login.")
    else:
        print("Register failed.")

def login():
    global token, username
    user = input("username: ")
    pw = getpass("password: ")
    sc, res = api_post("/login", json_data={"username": user, "password": pw})
    if sc == 200 and "token" in res:
        token = res["token"]
        username = user
        print("Logged in.")
        
        if os.path.exists(DOWNLOAD_FOLDER):
            shutil.rmtree(DOWNLOAD_FOLDER)
        os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
        
        predownload_recommendations()
    else:
        print("Login failed:", res)

def upload():
    path = input("path to file to upload: ").strip()
    if not os.path.exists(path):
        print("File not found")
        return
    metadata = input("optional metadata as JSON (or empty): ").strip()
    if metadata == "":
        metadata = "{}"
    files = {"file": open(path, "rb")}
    data = {"metadata": metadata}
    sc, res = api_post("/upload", files=files, data=data)
    print(sc, res)

def list_images():
    q = input("search query (press enter for all): ").strip()
    params = {"q": q} if q else {}
    sc, res = api_get("/images", params=params)
    if sc == 200:
        for it in res:
            print(f"{it['id']}: {it['filename']} (uploader: {it['uploader']}, {it['upload_time']})")
    else:
        print("Error:", res)

def download_image_by_id(image_id):
    global token
    
    for ext in [".jpg", ".png", ".jpeg", ".gif", ".bmp", ".webp", ".bin"]:
        candidate = os.path.join(DOWNLOAD_FOLDER, f"{image_id}{ext}")
        if os.path.exists(candidate):
            # Found locally — no need to redownload
            print(f"Image {image_id} found locally at {candidate}")
            return candidate

    
    url = SERVER + f"/image/{image_id}/download"
    headers = {}
    if token:
        headers["X-Token"] = token

    r = requests.get(url, headers=headers, stream=True)
    if r.status_code != 200:
        try:
            print("Error:", r.json())
        except Exception:
            print("Download failed:", r.status_code, r.text)
        return None

    cd = r.headers.get("content-disposition", "")
    ext = None

    if "filename=" in cd:
        fname = cd.split("filename=")[-1].strip('" ')
        ext = os.path.splitext(fname)[-1]

    if not ext:
        content_type = r.headers.get("content-type", "")
        if "jpeg" in content_type:
            ext = ".jpg"
        elif "png" in content_type:
            ext = ".png"
        elif "gif" in content_type:
            ext = ".gif"
        elif "bmp" in content_type:
            ext = ".bmp"
        elif "webp" in content_type:
            ext = ".webp"
        else:
            ext = ".bin"

    save_path = os.path.join(DOWNLOAD_FOLDER, f"{image_id}{ext}")
    with open(save_path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)

    print(f"Downloaded image {image_id} -> {save_path}")
    return save_path

def open_image():
    image_id = input("image id to open: ").strip()
    if not image_id.isdigit():
        print("invalid")
        return
    image_id = int(image_id)
    
    p = download_image_by_id(image_id)
    if not p:
        return
    try:
        im = Image.open(p)
        im.show()
    except Exception as e:
        print("Cannot open image locally:", e)
        return
    
    sc, res = api_post(f"/image/{image_id}/open")
    print("server open result:", sc, res)

def predownload_recommendations():
    print("Fetching recommendations...")
    sc, recs = api_get("/recommendations")
    if sc != 200:
        print("Couldn't get recommendations.", recs)
        return
    
    top = recs[:5]
    for r in top:
        iid = r["id"]
        print("Pre-downloading:", r.get("filename"), "id", iid)
        p = download_image_by_id(iid)
        if p:
            print("Saved to:", p)

def search_and_predownload():
    q = input("search query: ").strip()
    sc, res = api_get("/images", params={"q": q})
    if sc != 200:
        print("error", res)
        return
    print("Results:")
    for it in res:
        print(f"{it['id']}: {it['filename']}")
    
    sc2, recs = api_get("/recommendations")
    if sc2 == 200:
        res_ids = {it['id'] for it in res}
        filtered = [r for r in recs if r["id"] in res_ids][:3]
        for r in filtered:
            print("Pre-downloading recommended:", r)
            download_image_by_id(r["id"])
    else:
        print("No recommendations available.")

def get_meta():
    iid = input("image id: ").strip()
    sc,res = api_get(f"/image/{iid}/meta")
    print(sc,res)

def check_blockchain():
    sc,res = api_get("/blockchain/integrity")
    print(sc,res)

def menu():
    while True:
        print("\nMenu:")
        print("1. Register")
        print("2. Login")
        print("3. Upload Image")
        print("4. List / Search Images")
        print("5. Open Image by ID")
        print("6. Get Image Metadata")
        print("7. Search and Predownload Likely Images")
        print("8. Check blockchain integrity")
        print("0. Exit")
        c = input("choose: ").strip()
        if c == "1":
            register()
        elif c == "2":
            login()
        elif c == "3":
            upload()
        elif c == "4":
            list_images()
        elif c == "5":
            open_image()
        elif c == "6":
            get_meta()
        elif c == "7":
            search_and_predownload()
        elif c == "8":
            check_blockchain()
        elif c == "0":
            break
        else:
            print("unknown")

if __name__ == "__main__":
    print("Client console UI")
    menu()
