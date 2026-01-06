import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';

const CHANNELS = ['EcoCash', 'ZIPIT', 'Bank', 'Paynow', 'Cash', 'Other'];
const STATUSES = ['Expected', 'Received', 'Pending', 'Missing'];

export default function CreateTransaction() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [formData, setFormData] = useState({
        amount: '',
        channel: 'EcoCash',
        direction: 'Incoming',
        status: 'Expected',
        reference: '',
        transaction_date: new Date().toISOString().split('T')[0],
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (parseFloat(formData.amount) <= 0) {
            setError('Amount must be positive');
            return;
        }

        setLoading(true);

        try {
            await api.post('/transactions', {
                ...formData,
                amount: parseFloat(formData.amount),
            });
            navigate('/dashboard');
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to create transaction');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <header className="bg-white shadow-sm">
                <div className="max-w-2xl mx-auto px-4 py-4">
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="text-gray-600 hover:text-gray-900"
                    >
                        ← Back to Dashboard
                    </button>
                </div>
            </header>

            <main className="max-w-2xl mx-auto px-4 py-8">
                <div className="card">
                    <h1 className="text-2xl font-bold mb-6">New Transaction</h1>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && (
                            <div className="bg-danger-50 text-danger-600 px-4 py-3 rounded-lg">
                                {error}
                            </div>
                        )}

                        <div>
                            <label htmlFor="amount" className="block text-sm font-medium mb-2">
                                Amount *
                            </label>
                            <input
                                id="amount"
                                name="amount"
                                type="number"
                                step="0.01"
                                value={formData.amount}
                                onChange={handleChange}
                                className="input-field text-2xl"
                                required
                                autoFocus
                            />
                        </div>

                        <div>
                            <label htmlFor="channel" className="block text-sm font-medium mb-2">
                                Channel *
                            </label>
                            <select
                                id="channel"
                                name="channel"
                                value={formData.channel}
                                onChange={handleChange}
                                className="input-field"
                                required
                            >
                                {CHANNELS.map((channel) => (
                                    <option key={channel} value={channel}>
                                        {channel}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label htmlFor="status" className="block text-sm font-medium mb-2">
                                Status *
                            </label>
                            <select
                                id="status"
                                name="status"
                                value={formData.status}
                                onChange={handleChange}
                                className="input-field"
                                required
                            >
                                {STATUSES.map((status) => (
                                    <option key={status} value={status}>
                                        {status}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label htmlFor="reference" className="block text-sm font-medium mb-2">
                                Reference / Note *
                            </label>
                            <textarea
                                id="reference"
                                name="reference"
                                value={formData.reference}
                                onChange={handleChange}
                                className="input-field"
                                rows="3"
                                required
                            />
                        </div>

                        <div>
                            <label htmlFor="transaction_date" className="block text-sm font-medium mb-2">
                                Date *
                            </label>
                            <input
                                id="transaction_date"
                                name="transaction_date"
                                type="date"
                                value={formData.transaction_date}
                                onChange={handleChange}
                                className="input-field"
                                required
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="btn-primary w-full text-lg py-4"
                        >
                            {loading ? 'Creating...' : 'Create Transaction'}
                        </button>
                    </form>
                </div>
            </main>
        </div>
    );
}
