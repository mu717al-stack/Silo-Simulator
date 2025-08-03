import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Password protection
st.set_page_config(page_title="Silo Simulator", layout="wide")
password = st.text_input("🔒 Enter password to access the app:", type="password")
if password != "Alumina123":
    st.warning("Access denied. Please enter the correct password.")
    st.stop()

MAX_CAPACITY = 65000
DAILY_CONSUMPTION = 3400
MIN_THRESHOLD = 10000
WARNING_THRESHOLD = 20000

class Silo:
    def __init__(self, name):
        self.name = name
        self.layers = []
        self.history = {}

    def add_shipment(self, quantity, spec):
        total = self.get_total_quantity()
        if total + quantity > MAX_CAPACITY:
            st.warning(f"{self.name} will exceed max capacity of 65,000 tons.")
        self.layers.insert(0, {'quantity': quantity, 'spec': spec})
        self._trim_to_capacity()

    def _trim_to_capacity(self):
        total = self.get_total_quantity()
        while total > MAX_CAPACITY and self.layers:
            excess = total - MAX_CAPACITY
            if self.layers[-1]['quantity'] <= excess:
                total -= self.layers[-1]['quantity']
                self.layers.pop()
            else:
                self.layers[-1]['quantity'] -= excess
                total -= excess

    def consume(self, amount):
        consumed = []
        remaining = amount
        while remaining > 0 and self.layers:
            layer = self.layers[-1]
            if layer['quantity'] <= remaining:
                consumed.append((layer['spec'], layer['quantity']))
                remaining -= layer['quantity']
                self.layers.pop()
            else:
                consumed.append((layer['spec'], remaining))
                layer['quantity'] -= remaining
                remaining = 0
        return consumed

    def restore_consumed(self, consumed_layers):
        for spec, qty in reversed(consumed_layers):
            self.layers.append({'quantity': qty, 'spec': spec})

    def get_total_quantity(self):
        return sum(layer['quantity'] for layer in self.layers)

    def get_layer_info(self):
        return [(layer['spec'], layer['quantity']) for layer in self.layers]

def draw_silo(silo, ax):
    bottom = 0
    for layer in reversed(silo.layers):
        height = layer['quantity']
        ax.bar(0, height, bottom=bottom, label=layer['spec'])
        bottom += height

    # Threshold lines
    ax.axhline(MIN_THRESHOLD, color='red', linestyle='--', linewidth=1.5, label="Critical Level (10,000t)")
    ax.axhline(WARNING_THRESHOLD, color='orange', linestyle='--', linewidth=1.5, label="Low Warning (20,000t)")

    ax.set_ylim(0, MAX_CAPACITY)
    ax.set_title(f"{silo.name} - {silo.get_total_quantity()} Tons")
    ax.axes.get_xaxis().set_visible(False)
    ax.legend(fontsize=6, loc='upper right')

# Session state
if 'silo1' not in st.session_state:
    st.session_state.silo1 = Silo("Silo 1")
    st.session_state.silo2 = Silo("Silo 2")
    st.session_state.current_silo = st.session_state.silo1
    st.session_state.current_date = datetime.today().date()
    st.session_state.history = {}
    st.session_state.log = []

# Reset
if st.button("🧹 Reset All Data"):
    st.session_state.silo1 = Silo("Silo 1")
    st.session_state.silo2 = Silo("Silo 2")
    st.session_state.current_silo = st.session_state.silo1
    st.session_state.current_date = datetime.today().date()
    st.session_state.history = {}
    st.session_state.log = []
    st.success("All data has been reset.")

# Title
st.title("🛢️ Alumina Silo Simulator")

# Active Silo switch
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔄 Switch Silo"):
        st.session_state.current_silo = (
            st.session_state.silo2 if st.session_state.current_silo == st.session_state.silo1 else st.session_state.silo1
        )
with col2:
    st.subheader(f"Current Silo: {st.session_state.current_silo.name}")

# Add shipment
qty = st.number_input("Quantity (tons):", min_value=1, max_value=65000, value=1000)
spec = st.text_input("Spec Type:", value="Type A")
if st.button("➕ Add Shipment"):
    st.session_state.current_silo.add_shipment(qty, spec)

# Date controls
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("◀ Previous Day"):
        if st.session_state.current_date > datetime.today().date():
            st.session_state.current_date -= timedelta(days=1)
            if st.session_state.log and st.session_state.log[-1].startswith(str(st.session_state.current_date)):
                st.session_state.log.pop()
            if st.session_state.current_date in st.session_state.history:
                s1_layers, s2_layers = st.session_state.history[st.session_state.current_date]['layers']
                st.session_state.silo1.layers = [layer.copy() for layer in s1_layers]
                st.session_state.silo2.layers = [layer.copy() for layer in s2_layers]
with col2:
    st.markdown(f"### 📅 {st.session_state.current_date}")
with col3:
    if st.button("Next Day ▶"):
        st.session_state.history[st.session_state.current_date] = {
            'layers': (
                [layer.copy() for layer in st.session_state.silo1.layers],
                [layer.copy() for layer in st.session_state.silo2.layers]
            )
        }
        consumed = st.session_state.current_silo.consume(DAILY_CONSUMPTION)
        st.session_state.current_date += timedelta(days=1)
        if consumed:
            st.session_state.log.append(
                f"{st.session_state.current_date - timedelta(days=1)} | {st.session_state.current_silo.name} | "
                + " + ".join([f"{qty}t of {spec}" for spec, qty in consumed])
            )

# Plot both silos
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
draw_silo(st.session_state.silo1, ax1)
draw_silo(st.session_state.silo2, ax2)
st.pyplot(fig)

# History
st.subheader("📜 Consumption History")
if st.session_state.log:
    for entry in reversed(st.session_state.log):
        st.markdown(f"- {entry}")
