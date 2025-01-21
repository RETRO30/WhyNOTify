from flask import Flask, jsonify, request, session

from utils.logger import logger

app = Flask(__name__)

# Полные данные коллекции
FULL_DATA = {
    "ok": True,
    "data": {
        "characters": [
            {
                "id": 4,
                "collection_id": 8,
                "name": "DOGS Pixel",
                "description": "DOGS pixels that simply bark",
                "stickers": [
                    286,
                    287,
                    288,
                    289,
                    290,
                    291,
                    292,
                    293,
                    294,
                    295,
                    296,
                    297,
                    298,
                    299,
                    300,
                    301,
                    302,
                    303,
                    304,
                    305,
                    306,
                    307,
                    308,
                    309,
                    310,
                    311,
                    312,
                    313,
                    314,
                    315
                ],
                "price": 512,
                "left": 0,
                "supply": 4096,
                "attributes": {},
            },
        ],           
    }
}


@app.route('/api/v1/collection/8', methods=['GET'])
def get_collection():
    # Последующие запросы возвращают полные данные
    logger.info('GET /api/v1/collection/8')
    logger.info(f"send {len(FULL_DATA['data']['characters'])} characters")
    return jsonify(FULL_DATA)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
