import pandas as pd
from src.api.gsepro import GSEClient

def main():
    gse = GSEClient()

    clientes = gse.clientes_regiones()
    cliente = next((c for c in clientes if c["idCliente"] == 160), None)

    if not cliente:
        print("Cliente 160 no encontrado")
        return

    # 👇 Aquí empieza lo importante
    with pd.ExcelWriter("equipos_7_Eleven.xlsx", engine="openpyxl") as writer:

        for region in cliente["regiones"]:
            idRegion = region["idRegion"]
            nombreRegion = region["nombre"]

            print(f"Procesando región: {nombreRegion}")

            equipos = gse.hvac_valores(
                cliente["idCliente"],
                "2026-03-14",
                "2026-03-14",
                idRegion
            )

            equipos_filtrados = [
                e for e in equipos
                if str(e.get("Tecnología", "")).lower() != "sensibo"
            ]

            if not equipos_filtrados:
                print(f"Sin datos en {nombreRegion}")
                continue

            df = pd.DataFrame(equipos_filtrados)

            # 👇 Extra PRO: agrega el nombre de región como columna
            df["RegionNombre"] = nombreRegion

            # 👇 Evitar error por nombres largos o inválidos
            sheet_name = nombreRegion[:31].replace("/", "-")

            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print("✅ Excel generado: equipos_7_Eleven.xlsx")


if __name__ == "__main__":
    main()