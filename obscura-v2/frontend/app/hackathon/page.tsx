"use client";

import { useState } from "react";
import { CitadelService, ConductorService, PaymentsService } from "@/lib/api/services";

export default function HackathonPage() {
    // Zcash State
    const [paymentAddress, setPaymentAddress] = useState("");
    const [paymentStatus, setPaymentStatus] = useState("idle");

    // Nillion State
    const [apiKey, setApiKey] = useState("");
    const [storeId, setStoreId] = useState("");
    const [nillionStatus, setNillionStatus] = useState("idle");

    // NEAR State
    const [executionResult, setExecutionResult] = useState<any>(null);
    const [nearStatus, setNearStatus] = useState("idle");

    // 1. Zcash Flow
    const handleSubscribe = async () => {
        setPaymentStatus("generating_address");
        try {
            const res = await PaymentsService.subscribe("user_123", "pro");
            setPaymentAddress(res.payment_address);
            setPaymentStatus("waiting_for_payment");
        } catch (e) {
            console.error(e);
            setPaymentStatus("error");
        }
    };

    const handleSimulatePayment = async () => {
        if (!paymentAddress) return;
        try {
            await PaymentsService.simulatePayment(paymentAddress);
            const check = await PaymentsService.checkPayment(paymentAddress);
            if (check.received) {
                setPaymentStatus("paid");
            }
        } catch (e) {
            console.error(e);
        }
    };

    // 2. Nillion Flow
    const handleStoreKey = async () => {
        setNillionStatus("storing");
        try {
            const res = await CitadelService.storeSecret(apiKey, "binance_api_key");
            setStoreId(res.store_id);
            setNillionStatus("stored");
        } catch (e) {
            console.error(e);
            setNillionStatus("error");
        }
    };

    // 3. NEAR Flow
    const handleExecute = async () => {
        setNearStatus("executing");
        try {
            const res = await ConductorService.executeTrade("user_123", "base", "swap", {
                from: "USDC",
                to: "ETH",
                amount: 100
            });
            setExecutionResult(res);
            setNearStatus("executed");
        } catch (e) {
            console.error(e);
            setNearStatus("error");
        }
    };

    return (
        <div className="min-h-screen bg-black text-white p-8 font-sans">
            <h1 className="text-4xl font-bold mb-8 text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600">
                Obscura V2: The Grand Slam
            </h1>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">

                {/* Zcash Card */}
                <div className="border border-gray-800 p-6 rounded-xl bg-gray-900/50">
                    <h2 className="text-2xl font-bold mb-4 text-yellow-400">1. Shielded Subscription</h2>
                    <p className="text-gray-400 mb-4">Pay with ZEC to unlock the platform.</p>

                    {paymentStatus === "idle" && (
                        <button
                            onClick={handleSubscribe}
                            className="bg-yellow-500 hover:bg-yellow-600 text-black font-bold py-2 px-4 rounded w-full"
                        >
                            Subscribe (0.1 ZEC)
                        </button>
                    )}

                    {paymentStatus === "waiting_for_payment" && (
                        <div className="space-y-4">
                            <div className="bg-gray-800 p-3 rounded break-all font-mono text-xs">
                                {paymentAddress}
                            </div>
                            <div className="flex items-center justify-center space-x-2 animate-pulse text-yellow-500">
                                <span>Waiting for ZEC...</span>
                            </div>
                            <button
                                onClick={handleSimulatePayment}
                                className="border border-yellow-500 text-yellow-500 hover:bg-yellow-500/10 py-1 px-3 rounded text-sm w-full"
                            >
                                (Dev) Simulate Payment
                            </button>
                        </div>
                    )}

                    {paymentStatus === "paid" && (
                        <div className="text-green-400 font-bold text-center border border-green-500/30 bg-green-500/10 p-4 rounded">
                            ✅ Subscription Active
                        </div>
                    )}
                </div>

                {/* Nillion Card */}
                <div className="border border-gray-800 p-6 rounded-xl bg-gray-900/50">
                    <h2 className="text-2xl font-bold mb-4 text-blue-400">2. The Glass Vault</h2>
                    <p className="text-gray-400 mb-4">Store API keys in Nillion Network.</p>

                    <div className="space-y-4">
                        <input
                            type="text"
                            placeholder="Enter Exchange API Key"
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-white focus:outline-none focus:border-blue-500"
                        />
                        <button
                            onClick={handleStoreKey}
                            disabled={!apiKey || nillionStatus === "stored"}
                            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold py-2 px-4 rounded w-full"
                        >
                            {nillionStatus === "stored" ? "Stored in nilDB" : "Encrypt & Store"}
                        </button>

                        {storeId && (
                            <div className="text-xs text-gray-500 font-mono mt-2">
                                Store ID: {storeId}
                            </div>
                        )}
                    </div>
                </div>

                {/* NEAR Card */}
                <div className="border border-gray-800 p-6 rounded-xl bg-gray-900/50">
                    <h2 className="text-2xl font-bold mb-4 text-green-400">3. Universal Remote</h2>
                    <p className="text-gray-400 mb-4">Execute trades via NEAR Chain Signatures.</p>

                    <div className="space-y-4">
                        <div className="bg-gray-800 p-3 rounded text-sm text-gray-300">
                            <div>Action: Swap USDC -> ETH</div>
                            <div>Chain: Base</div>
                        </div>

                        <button
                            onClick={handleExecute}
                            disabled={paymentStatus !== "paid" || nillionStatus !== "stored"}
                            className="bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded w-full"
                        >
                            Execute via NEAR MPC
                        </button>

                        {paymentStatus !== "paid" && (
                            <p className="text-xs text-red-400 text-center">Requires Subscription</p>
                        )}

                        {executionResult && (
                            <div className="mt-4 p-3 bg-gray-800 rounded text-xs font-mono overflow-hidden">
                                <div className="text-green-400 mb-1">Success!</div>
                                <div>Tx: {executionResult.tx_hash}</div>
                                <div className="mt-1 text-gray-500">Signed by NEAR MPC</div>
                            </div>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
}
