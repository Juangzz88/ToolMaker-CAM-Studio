import os
import shutil
import subprocess

def build_distributable_app():
    print("==========================================================")
    print(" 🛠️  INICIANDO CONSTRUCCIÓN DE RELEASE COMERCIAL")
    print("==========================================================")

    release_dir = "release_build"
    
    # 1. Limpiar directorio previo si existe
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
        print(f"🧹 Carpeta previa '{release_dir}' eliminada.")

    os.makedirs(release_dir, exist_ok=True)

    # 2. Ofuscar y compilar la carpeta engineering/ con PyArmor
    print("🔒 Compilando y protegiendo el motor físico (engineering/)...")
    try:
        subprocess.run(
            ["pyarmor", "gen", "-O", os.path.join(release_dir, "engineering"), "engineering/"],
            check=True
        )
        print("✅ Motor físico compilado con éxito.")
    except Exception as e:
        print(f"❌ Error durante la compilación con PyArmor: {e}")
        return

    # 3. Copiar el resto de las carpetas y archivos necesarios
    carpetas_a_copiar = ["routes", "templates", "static", "core"]
    archivos_a_copiar = ["app.py", "requirements.txt", "public_key.pem"]

    for carpeta in carpetas_a_copiar:
        if os.path.exists(carpeta):
            shutil.copytree(carpeta, os.path.join(release_dir, carpeta))
            print(f"📦 Carpeta '{carpeta}' copiada a release.")

    for archivo in archivos_a_copiar:
        if os.path.exists(archivo):
            shutil.copy2(archivo, os.path.join(release_dir, archivo))
            print(f"📄 Archivo '{archivo}' copiado a release.")

    print("\n==========================================================")
    print(f" 🎉 CONSTRUCCIÓN FINALIZADA CON ÉXITO")
    print(f" La versión comercial para el cliente está en: ./{release_dir}/")
    print(" NOTA: Recuerda NO incluir 'private_key.pem' ni 'crear_licencia_dev.py'.")
    print("==========================================================")

if __name__ == "__main__":
    build_distributable_app()