import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../utils/api';

export default function Dashboard() {
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const { logout } = useAuth();

    useEffect(() => {
        fetchDashboardData();
    }, [date]);

    const fetchDashboardData = async () => {
        setLoading(true);
        try {
            const response = await api.get(`/dashboard/daily?target_date=${date}`);
            setData(response.data);
        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (amount) => {
        return `$${amount.toFixed(2)}`;
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-xl">Loading...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <header className="bg-white shadow-sm">
                <div className="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
                    <h1 className="text-2xl font-bold">ClearLedger</h1>
                    <button onClick={logout} className="text-gray-600 hover:text-gray-900">
                        Logout
                    </button>
                </div>
            </header>

            <main className="max-w-4xl mx-auto px-4 py-8">
                <div className="mb-6 flex justify-between items-center">
                    <div>
                        <label htmlFor="date" className="block text-sm font-medium mb-2">
                            Select Date
                        </label>
                        <input
                            id="date"
                            type="date"
                            value={date}
                            onChange={(e) => setDate(e.target.value)}
                            className="input-field"
                        />
                    </div>
                    <Link to="/create-transaction" className="btn-primary">
                        + New Transaction
                    </Link>
                </div>

                {/* Daily Totals */}
                <div className="card mb-8">
                    <h2 className="text-xl font-bold mb-4">Daily Truth</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                            <div className="text-sm text-gray-600 mb-1">Expected</div>
                            <div className="text-2xl font-bold text-warning-600">
                                {formatCurrency(data?.totals?.expected || 0)}
                            </div>
                        </div>
                        <div className="text-center">
                            <div className="text-sm text-gray-600 mb-1">Received</div>
                            <div className="text-2xl font-bold text-success-600">
                                {formatCurrency(data?.totals?.received || 0)}
                            </div>
                        </div>
                        <div className="text-center">
                            <div className="text-sm text-gray-600 mb-1">Pending</div>
                            <div className="text-2xl font-bold text-primary-600">
                                {formatCurrency(data?.totals?.pending || 0)}
                            </div>
                        </div>
                        <div className="text-center">
                            <div className="text-sm text-gray-600 mb-1">Missing</div>
                            <div className="text-2xl font-bold text-danger-600">
                                {formatCurrency(data?.totals?.missing || 0)}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Channel Breakdown */}
                <div className="card">
                    <h2 className="text-xl font-bold mb-4">By Channel</h2>
                    {data?.channels?.length > 0 ? (
                        <div className="space-y-3">
                            {data.channels.map((channel) => (
                                <div
                                    key={channel.channel}
                                    className="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
                                >
                                    <div>
                                        <div className="font-semibold">{channel.channel}</div>
                                        <div className="text-sm text-gray-600">
                                            {channel.count} transaction{channel.count !== 1 ? 's' : ''}
                                        </div>
                                    </div>
                                    <div className="text-lg font-bold">
                                        {formatCurrency(channel.total)}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-gray-600 text-center py-8">
                            No transactions for this date
                        </p>
                    )}
                </div>
            </main>
        </div>
    );
}
