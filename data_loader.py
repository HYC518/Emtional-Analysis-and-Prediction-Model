import pandas as pd
class DataLoader:
    @staticmethod
    def load_csv(file_path: str) -> pd.DataFrame:
        return pd.read_csv(file_path)

    @staticmethod
    def load_excel(file_path: str) -> pd.DataFrame:
        return pd.read_excel(file_path)

    @staticmethod
    def customize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        df = df.drop_duplicates()
        df = df.ffill()
        return df