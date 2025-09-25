from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
import sys

# Проверяем наличие библиотеки pypostal
try:
    from postal.parser import parse_address
    from postal.expand import expand_address
    POSTAL_AVAILABLE = True
except ImportError:
    print("ВНИМАНИЕ: Библиотека pypostal не установлена. Будет использоваться заглушка.")
    exit(1)

app = Flask(__name__)
CORS(app)  # Разрешаем кросс-доменные запросы


@app.route('/parse', methods=['GET', 'POST'])
def parse():
    """
    Парсинг адреса с помощью pypostal
    
    Поддерживает как GET, так и POST запросы:
    - GET: ожидает параметр запроса 'address'
    - POST: ожидает JSON с полем 'address'
    
    Возвращает структурированный адрес в виде словаря
    """
    # Получаем адрес из запроса
    if request.method == 'GET':
        address = request.args.get('address')
        print(f"[DEBUG] Получен GET запрос с адресом: {address}")
    else:  # POST
        if not request.is_json:
            return jsonify({"error": "Ожидается JSON"}), 400
        data = request.get_json()
        address = data.get('address')
        print(f"[DEBUG] Получен POST запрос с адресом: {address}")
    
    if not address:
        error_response = {"error": "Параметр 'address' обязателен"}
        print(f"[DEBUG] Ошибка: {error_response}")
        return jsonify(error_response), 400
    
    try:
        parsed = []
        # Парсинг адреса
        if POSTAL_AVAILABLE:
            parsed = parse_address(address)
        else:
            raise Exception("Библиотека pypostal не установлена")
        result = {}
        for value, component in parsed:
            result[component] = value
        print(f"[DEBUG] Отправляем результат: {result}")
        return jsonify(result)
    
    except Exception as e:
        error_message = f"Ошибка при парсинге адреса: {str(e)}"
        print(error_message)
        print("[DEBUG] Трассировка ошибки:")
        traceback.print_exc(file=sys.stdout)
        return jsonify({"error": error_message}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка работоспособности сервиса"""
    print("[DEBUG] Получен запрос на проверку работоспособности")
    status = {"status": "ok", "pypostal_available": POSTAL_AVAILABLE}
    print(f"[DEBUG] Отправляем статус: {status}")
    return jsonify(status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)