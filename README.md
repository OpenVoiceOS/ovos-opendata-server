## **OVOS Metrics Collector 📊**  

A **FastAPI service** for collecting anonymized OVOS usage metrics with an **interactive Streamlit dashboard** for visualization.  

🚀 **Features:**  
- ✅ **FastAPI backend** to store utterance logs  
- ✅ **PostgreSQL database** for structured storage  
- ✅ **Streamlit dashboard** for data analysis  
- ✅ **Filters, charts, and data export (CSV & JSON)**  
- ✅ **Dockerized setup for easy deployment**  


---

## **🛠️ Setup & Installation**  

### **1️⃣ Clone the Repository**  
```bash
git clone https://github.com/TigreGotico/metrics-server-docker
cd metrics-server-docker
```

### **3️⃣ Start the Services**  
```bash
docker-compose up --build -d
```
This will start:  
- **FastAPI server** on `http://localhost:8000`  
- **PostgreSQL database**  
- **Streamlit dashboard** on `http://localhost:8501`  

---

## **📝 API Usage**  

![img_1.png](img_1.png)
### **1️⃣ Submit Data (POST)**  
Send anonymized metrics from OVOS:  
```bash
curl -X POST "http://localhost:8000/metrics" \
     -H "Content-Type: application/json" \
     -H "User-Agent: ovos-core-metrics" \
     -d '{
           "utterance": "What’s the weather?",
           "intent": "ask_weather",
           "language": "en"
         }'
```
>NOTE: the user agent **must** be `ovos-core-metrics` otherwise the request is ignored

---

## **📊 Streamlit Dashboard**  


1️⃣ **Open your browser:** `http://localhost:8501`  
2️⃣ **Features:**  
   - 📌 **Filter** by **date range, language, and intent**  
   - 📊 **Pie charts** for **intent & language distribution**  
   - 📥 **Export** data to **CSV & JSON**  
   - 🔄 **Live updates & refresh button**  

![img_3.png](img_3.png)
![img_2.png](img_2.png)
![img.png](img.png)
---


## **🤝 Contributing**  
1. **Fork the repo** & create a new branch  
2. **Make your changes** & ensure tests pass  
3. **Submit a pull request** 🎉  

---

## **📝 License**  
MIT License - Feel free to use and modify.  
