import React, { useState, useEffect } from 'react';
import { Layout, Menu, Bell, Settings, User } from 'lucide-react';
import EmailList from './components/EmailList';
import DraftEditor from './components/DraftEditor';
import StatsWidget from './components/StatsWidget';
import api from './api';

function App() {
  const [emails, setEmails] = useState([]);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [stats, setStats] = useState({ processed: 124, saved: 12, accuracy: 98 });
  const [loading, setLoading] = useState(true);

  // Load mock data or fetch from API
  useEffect(() => {
    const fetchEmails = async () => {
      try {
        const response = await api.get('/emails');
        setEmails(response.data);
      } catch (error) {
        console.error("Failed to fetch emails", error);

        // Mock Data for demonstration if API fails or is unreachable
        const mockEmails = [
          {
            id: '1',
            sender: 'Alice Smith',
            subject: 'Meeting Request: Project Alpha',
            body: 'Hi Rayan,\n\nCould we meet tomorrow at 10 AM to discuss the Alpha project timeline?\n\nBest,\nAlice',
            classification: { intent: 'meeting', urgency: 'medium' },
            generatedDraft: "Hi Alice,\n\nThanks for reaching out. Yes, I'm available at 10 AM tomorrow. Looking forward to discussing the timeline.\n\nBest,\nRayan"
          },
          {
            id: '2',
            sender: 'Support Team',
            subject: 'Your Ticket #12345',
            body: 'Your issue has been resolved. Please rate our service.',
            classification: { intent: 'notification', urgency: 'low' },
            generatedDraft: "Thank you for the update."
          },
          {
            id: '3',
            sender: 'Bob Johnson',
            subject: 'URGENT: Server Down',
            body: 'The production server is unresponsive on port 8080. We need immediate assistance.',
            classification: { intent: 'support', urgency: 'high' },
            generatedDraft: "Hi Bob,\n\nI'm looking into this immediately. I'll update you shortly.\n\nBest,\nRayan"
          }
        ];

        setEmails(mockEmails);
      } finally {
        setLoading(false);
      }
    };

    fetchEmails();
  }, []);

  const handleAction = async (action, email) => {
    if (action === 'approve') {
      alert(`Email sent to ${email.sender}!`);
      // Here we would call api.post('/send', { ... })
      // And remove from list
      setEmails(emails.filter(e => e.id !== email.id));
      setSelectedEmail(null);
    } else if (action === 'discard') {
      setEmails(emails.filter(e => e.id !== email.id));
      setSelectedEmail(null);
    } else if (action === 'regenerate') {
      // Call API to regenerate
      alert('Regenerating draft...');
    }
  };

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900 font-sans text-gray-900 dark:text-gray-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col hidden md:flex">
        <div className="p-6 flex items-center space-x-3">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <Layout className="text-white w-5 h-5" />
          </div>
          <span className="text-xl font-bold tracking-tight">AutoResponse.ai</span>
        </div>

        <nav className="flex-1 px-4 space-y-2 mt-4">
          <a href="#" className="flex items-center space-x-3 px-4 py-3 bg-indigo-50 dark:bg-gray-800 text-indigo-600 dark:text-white rounded-xl transition-colors font-medium">
            <Layout size={20} />
            <span>Dashboard</span>
          </a>
          <a href="#" className="flex items-center space-x-3 px-4 py-3 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-xl transition-colors font-medium">
            <Settings size={20} />
            <span>Settings</span>
          </a>
        </nav>

        <div className="p-4 border-t border-gray-100 dark:border-gray-800">
          <div className="flex items-center space-x-3 px-4 py-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-pink-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
              R
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">Rayan</p>
              <p className="text-xs text-gray-400">Pro Plan</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="h-16 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between px-6">
          <h1 className="text-lg font-semibold text-gray-700 dark:text-gray-200">Waitlist Review</h1>
          <div className="flex items-center space-x-4">
            <button className="p-2 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg relative">
              <Bell size={20} />
              <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white dark:border-gray-900"></span>
            </button>
          </div>
        </header>

        {/* Dashboard Content */}
        <div className="flex-1 overflow-hidden p-6 flex flex-col">
          <StatsWidget stats={stats} />

          <div className="flex-1 bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden flex">
            <EmailList
              emails={emails}
              selectedId={selectedEmail?.id}
              onSelect={setSelectedEmail}
            />
            <DraftEditor
              email={selectedEmail}
              onAction={handleAction}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
