# 현재 파일(main.py)의 상위 상위 폴더를 프로젝트 루트로 설정
import os
import sys
import glob

# 1. 원본 유지 및 경로 자동 추가 로직
# main.py 파일의 위치를 기준으로 프로젝트 루트(YBIGTA... 폴더)를 찾습니다.
current_dir = os.path.dirname(os.path.abspath(__file__)) # preprocessing 폴더
project_root = os.path.abspath(os.path.join(current_dir, "../../")) # 최상위 루트

if project_root not in sys.path:
    sys.path.insert(0, project_root) # 최우선 순위로 경로 추가

from argparse import ArgumentParser
from typing import Dict, Type
from review_analysis.preprocessing.base_processor import BaseDataProcessor
from review_analysis.preprocessing.imdb_processor import ImdbDataProcessor



if project_root not in sys.path:
    sys.path.append(project_root)

# 모든 preprocessing 클래스를 예시 형식으로 적어주세요. 
# key는 "reviews_사이트이름"으로, value는 해당 처리를 위한 클래스
PREPROCESS_CLASSES: Dict[str, Type[BaseDataProcessor]] = {
    "reviews_imdb": ImdbDataProcessor,
    # key는 크롤링한 csv파일 이름으로 적어주세요! ex. reviews_naver.csv -> reviews_naver
}

REVIEW_COLLECTIONS = glob.glob(os.path.join(project_root, "database", "reviews_*.csv"))

def create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument('-o', '--output_dir', type=str, required=False, default = "../../database", help="Output file dir. Example: ../../database")
    parser.add_argument('-c', '--preprocessor', type=str, required=False, choices=PREPROCESS_CLASSES.keys(),
                        help=f"Which processor to use. Choices: {', '.join(PREPROCESS_CLASSES.keys())}")
    parser.add_argument('-a', '--all', action='store_true',
                        help="Run all data preprocessors. Default to False.")    
    return parser

if __name__ == "__main__":

    parser = create_parser()
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if args.all: 
        for csv_file in REVIEW_COLLECTIONS:
            base_name = os.path.splitext(os.path.basename(csv_file))[0]
            if base_name in PREPROCESS_CLASSES:
                preprocessor_class = PREPROCESS_CLASSES[base_name]
                preprocessor = preprocessor_class(csv_file, args.output_dir)
                preprocessor.preprocess()
                preprocessor.feature_engineering()
                preprocessor.save_to_database()
