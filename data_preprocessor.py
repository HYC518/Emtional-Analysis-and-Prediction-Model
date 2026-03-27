import json
import pandas as pd
from gemini_client import GeminiClient   
from data_loader import DataLoader        
from prompts import Prompts           


class DataPreprocessor:

    def __init__(self, gemini: GeminiClient):
        self._client = gemini

    def clean(self, df: pd.DataFrame) -> dict:
        original_count = len(df)

        df_clean = DataLoader.customize_dataframe(df)
        rows = df_clean.to_dict(orient='records')
        pre_count = len(rows)

        user_msg = f'Here are the rows to clean:\n{json.dumps(rows, indent=2, ensure_ascii=False)}'
        deep_cleaned = self._client.ask_json(Prompts.DATA_CLEANING, user_msg)

        usable    = [r for r in deep_cleaned if r.get('clean') is not False]
        discarded = [r for r in deep_cleaned if r.get('clean') is False]

        return {
            'usable': usable,
            'discarded': discarded,
            'stats': {
                'original_rows': original_count,
                'after_local_clean': pre_count,
                'after_ai_clean': len(usable),
                'discarded_count': len(discarded),
            }
        }
