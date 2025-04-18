// @ts-nocheck
import React, { useState, useEffect } from "react";
import ChatBox from "./components/ChatBox";
import Sidebar from "./components/Sidebar";
import ExpenseList from "./components/ExpenseList";
import axios from "axios";
import "./index.css";

const App = () => {
  const [expenses, setExpenses] = useState([]);

  useEffect(() => {
    // Fetch expenses from the backend
    axios.get("http://localhost:5000/expenses")
      .then(response => setExpenses(response.data))
      .catch(error => console.error("Error fetching expenses:", error));
  }, []);

  return (
    <div className="h-screen flex">
      <div className="flex-1 p-6 flex flex-col">
        <ChatBox />
      </div>
    </div>
  );
};

export default App;
