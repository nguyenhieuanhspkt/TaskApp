from tskt_parser.processor import TSKTProcessor


def main():

    processor = TSKTProcessor()

    ten_hang = "Gioăng chèn con lăn: 185 Joint sealant"

    thong_so = """
    Gioăng chèn con lăn: 185 Joint sealant
    - Kích thước: 9.5 x 15000 mm
    """

    print("========== INPUT ==========")
    print("Tên hàng:", ten_hang)
    print("Thông số:", thong_so)

    result = processor.process(ten_hang, thong_so)

    print("\n========== PARSER RESULT ==========")

    print("Product type :", result.get("product_type", ""))
    print("Model        :", result.get("model", ""))
    print("Maker        :", result.get("maker", ""))
    print("Missing info :", result.get("missing_info", ""))
    print("Suggestion   :", result.get("suggestion", ""))

    print("\n========== RAW RESULT DICT ==========")
    print(result)


if __name__ == "__main__":
    main()