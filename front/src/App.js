import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [message, setMessage] = useState('');
  const [fileLink, setFileLink] = useState('');

  const handleScrape = async () => {
    try {
      const response = await axios.get('http://localhost:5000/scrape');
      if (response.status === 200) {
        setMessage(response.data.message);
        setFileLink(response.data.file);
      }
    } catch (error) {
      setMessage('Error occurred while scraping');
    }
  };

  return (
    <div className="App">
      <h1>Flask Selenium Scraping</h1>
      <button onClick={handleScrape}>Start Scraping</button>
      <div>
        <p>{message}</p>
        {fileLink && <a href={`file:///${fileLink}`} target="_blank" rel="noopener noreferrer">Download the file</a>}
      </div>
    </div>
  );
}

export default App;
