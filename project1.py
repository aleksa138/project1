pip install streamlit requests
streamlit run app.py
import streamlit as st
import requests
import csv
import re
import time
import io

# ================================
# ИЗВЛЕЧЕНИЕ APP ID
# ================================
def extract_app_id(url):
    match = re.search(r'id(\d+)', url)
    return match.group(1) if match else None

# ================================
# ПОЛУЧЕНИЕ ОТЗЫВОВ
# ================================
def fetch_reviews(app_id, max_reviews=1000, country="ru"):
    reviews = []
    page = 1

    progress = st.progress(0)
    status_text = st.empty()

    while len(reviews) < max_reviews:
        url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"

        try:
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                st.warning(f"Ошибка запроса: {response.status_code}")
                break

            data = response.json()

            if "feed" not in data or "entry" not in data["feed"]:
                break

            entries = data["feed"]["entry"]

            if page == 1:
                entries = entries[1:]  # пропуск инфо о приложении

            if not entries:
                break

            for entry in entries:
                review = {
                    "author": entry.get("author", {}).get("name", {}).get("label", ""),
                    "rating": entry.get("im:rating", {}).get("label", ""),
                    "title": entry.get("title", {}).get("label", ""),
                    "review": entry.get("content", {}).get("label", ""),
                    "version": entry.get("im:version", {}).get("label", ""),
                    "date": entry.get("updated", {}).get("label", ""),
                    "country": country,
                    "developer_response": entry.get("im:reply", {}).get("content", {}).get("label", "")
                }

                reviews.append(review)

                if len(reviews) >= max_reviews:
                    break

            status_text.text(f"Собрано отзывов: {len(reviews)}")
            progress.progress(min(len(reviews) / max_reviews, 1.0))

            page += 1
            time.sleep(0.3)

        except Exception as e:
            st.error(f"Ошибка: {e}")
            break

    progress.empty()
    status_text.empty()

    return reviews

# ================================
# СОЗДАНИЕ CSV В ПАМЯТИ
# ================================
def convert_to_csv(reviews):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=reviews[0].keys())
    writer.writeheader()
    writer.writerows(reviews)
    return output.getvalue()

# ================================
# UI STREAMLIT
# ================================
st.set_page_config(page_title="App Store Reviews Parser", layout="centered")

st.title("📱 App Store Reviews Parser")
st.write("Сбор отзывов через официальный API Apple")

app_url = st.text_input("Вставь ссылку на приложение App Store")

max_reviews = st.slider("Количество отзывов", 100, 1000, 500)

if st.button("Собрать отзывы"):
    if not app_url:
        st.warning("Вставь ссылку")
    else:
        app_id = extract_app_id(app_url)

        if not app_id:
            st.error("Не удалось извлечь app_id")
        else:
            with st.spinner("Собираем отзывы..."):
                reviews = fetch_reviews(app_id, max_reviews)

            if reviews:
                csv_data = convert_to_csv(reviews)

                st.success(f"Готово! Собрано {len(reviews)} отзывов")

                st.download_button(
                    label="📥 Скачать CSV",
                    data=csv_data,
                    file_name="appstore_reviews.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Отзывы не найдены")