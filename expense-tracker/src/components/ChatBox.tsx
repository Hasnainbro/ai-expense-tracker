import { useState } from "react";
import { Send } from "lucide-react";
import { processQuery } from "../services/api.ts";
import "./Chatbox.css" // Import our API service

const SimpleChatBox = () => {
  const [messages, setMessages] = useState([
    { text: "Hello! How can I help you?", sender: "bot" },
  ]);
  
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = { text: input, sender: "user" };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInput("");
    
    try {
      const response = await processQuery(input);
    
      // Use the response message from the backend, or a fallback message
      const botMessage = { text: response.message || "I couldn't process that.", sender: "bot" };
    
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      // Extract error message from backend
      let errorMessage = "Something went wrong. Please try again.";
  
      if ((error as any).response && (error as any).response.data && (error as any).response.data.message) {
        errorMessage = (error as any).response.data.message; // Show backend error message
      }
  
      setMessages((prevMessages) => [...prevMessages, { text: errorMessage, sender: "bot" }]);
    }
  }
    
  return (
    <div className="chatbox">
      <div className="chatbox-messages">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`chatbox-message ${msg.sender === "user" ? "chatbox-message-user" : "chatbox-message-bot"}`}
          >
            {msg.text}
          </div>
        ))}
      </div>
      <div className="chatbox-input-container">
        <input
          className="chatbox-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button className="chatbox-send-button" onClick={sendMessage}>
          <Send size={18} />
        </button>
      </div>
    </div>
  );
};

const ExpenseList = () => {
  const expenses = [
    { id: 1, category: "Food", amount: "$20" },
    { id: 2, category: "Transport", amount: "$15" },
  ];

  return (
    <div className="border rounded-lg p-4 bg-white">
      <h2 className="font-bold">Expenses</h2>
      {expenses.map((expense) => (
        <div key={expense.id} className="p-2 border-b">
          {expense.category}: {expense.amount}
        </div>
      ))}
    </div>
  );
};
const App = () => {
  return (
    <div className="flex h-screen">
      <div className="flex-1 flex flex-col p-4">
        <SimpleChatBox />
      </div>
    </div>
  );
};

export default App;