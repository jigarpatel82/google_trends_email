"use client"
import { useState } from 'react';
import axios from 'axios';

export default function GoogleTrendsForm() {
  const [email, setEmail] = useState('');
  const [geo, setGeo] = useState('US');
  const [apiMethod, setApiMethod] = useState('interest over time');
  const [category, setCategory] = useState(0);
  const [keywords, setKeywords] = useState('');
  const [timeframe, setTimeframe] = useState('today 5-y');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const requestData = {
      email,
      geo,
      apiMethod,
      category,
      keywords: keywords.split(','),
      timeframe,
    };

    try {
      const response = await axios.post('/api/sendGoogleTrends', requestData);
      alert('Request sent successfully!');
    } catch (error) {
      console.error('Error sending request:', error);
    }
  };

  return (
<div>


<form onSubmit={handleSubmit} className="max-w-sm mx-auto">
  <div className='mb-5 mt-5' >

<h2 className='font-bold'>Google Trends Subscription</h2>
  </div>
  <div className="mb-5">
    <label htmlFor="email" className="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Your email</label>
    <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} id="email" className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder="name@email.com" required />
  </div>
  <div className="mb-5">
    <label htmlFor="geo" className="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Geo Location</label>
    <input type="text" value={geo} onChange={(e) => setGeo(e.target.value)} id="geo" className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" required />
  </div>
  <div className="mb-5">
    <label htmlFor="category" className="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Category</label>
    <input type="number" value={category} onChange={(e) => setCategory(parseInt(e.target.value))} id="category" className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" required />
  </div>
  <div className="mb-5">
    <label htmlFor="countries" className="block mb-2 text-sm font-medium text-gray-900 dark:text-white">API method</label>
    <select value={apiMethod} onChange={(e) => setApiMethod(e.target.value)} id="apiMethods" className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500">

        <option value="interest over time">Interest Over Time</option>
        <option value="trending searches">Trending Searches</option>
        <option value="interest by region">Interest by Region</option>
    </select>
  </div>
  <div className="mb-5">
    <label htmlFor="keywords" className="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Keywords (comma separated)</label>
    <input type="text" value={keywords} onChange={(e) => setKeywords(e.target.value)} id="keywords" className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" required />
  </div>
  <div className="mb-5">
    <label htmlFor="timeframe" className="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Timeframe</label>
    <input type="text" value={timeframe} onChange={(e) => setTimeframe(e.target.value)} id="timeframe" className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"  required />
  </div>

  <button type="submit" className="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm w-full sm:w-auto px-5 py-2.5 text-center dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">Submit</button>
</form>
    </div>
  );
}
