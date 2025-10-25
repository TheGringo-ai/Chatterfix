/**
 * 📊 ChatterFix CMMS - Customer Success Dashboard
 * Real-time customer health monitoring with live WebSocket updates
 * 
 * Features:
 * - Live health score gauges and churn probability charts
 * - At-risk customer alerts with AI recommendations
 * - Real-time WebSocket updates from customer success analytics
 * - Integration with Revenue Intelligence for ROI widgets
 * - Mobile-responsive design with Material-UI + Tailwind
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  IconButton,
  CircularProgress,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  Avatar,
  Badge,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Fab,
  Snackbar
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  Error,
  Refresh,
  FilterList,
  Download,
  Notifications,
  Phone,
  Email,
  Assignment,
  Timeline,
  PieChart,
  BarChart,
  Dashboard,
  People,
  AttachMoney,
  Speed,
  Autorenew,
  Close
} from '@mui/icons-material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { Line, Bar, Doughnut, Gauge } from 'react-chartjs-2';
import { format, formatDistanceToNow } from 'date-fns';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend
);

interface CustomerHealth {
  customer_id: string;
  company_name: string;
  health_score: number;
  health_status: 'excellent' | 'good' | 'warning' | 'critical' | 'churn_risk';
  churn_probability: number;
  churn_risk: 'low' | 'medium' | 'high' | 'critical';
  component_scores: {
    usage: number;
    engagement: number;
    satisfaction: number;
    value_realization: number;
  };
  key_metrics: {
    daily_active_users: number;
    monthly_active_users: number;
    feature_adoption_rate: number;
    support_tickets_30d: number;
    uptime_percentage: number;
    cost_savings_achieved: number;
  };
  trends: {
    usage: string;
    engagement: string;
    satisfaction: string;
  };
  recommendations: {
    risk_factors: string[];
    success_recommendations: string[];
    intervention_priority: string;
  };
  last_updated: string;
}

interface CustomerKPIs {
  overview: {
    total_customers: number;
    active_customers: number;
    at_risk_customers: number;
    churned_customers_30d: number;
  };
  health_metrics: {
    avg_health_score: number;
    avg_churn_probability: number;
    nps_score: number;
  };
  distributions: {
    health_status: Record<string, number>;
    churn_risk: Record<string, number>;
  };
  financial_metrics: {
    monthly_recurring_revenue: number;
    customer_lifetime_value: number;
    customer_acquisition_cost: number;
    ltv_cac_ratio: number;
  };
  retention_rates: {
    retention_30d: number;
    retention_90d: number;
    retention_12m: number;
  };
  insights: {
    top_risk_factors: Array<{ factor: string; frequency: number }>;
    interventions_needed: number;
  };
  last_updated: string;
}

interface AtRiskCustomer {
  customer_id: string;
  company_name: string;
  last_health_score: number;
  predicted_churn_score: number;
  intervention_priority: string;
  risk_factors: string[];
  last_updated: string;
}

const CustomerSuccessDashboard: React.FC = () => {
  // State management
  const [kpis, setKpis] = useState<CustomerKPIs | null>(null);
  const [atRiskCustomers, setAtRiskCustomers] = useState<AtRiskCustomer[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState<string[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(`ws://localhost:8012/ws/customer-health`);
        
        ws.onopen = () => {
          setIsConnected(true);
          setWebsocket(ws);
          console.log('Connected to customer health WebSocket');
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
          } catch (err) {
            console.error('Error parsing WebSocket message:', err);
          }
        };
        
        ws.onclose = () => {
          setIsConnected(false);
          setWebsocket(null);
          console.log('WebSocket connection closed');
          
          // Reconnect after 5 seconds
          setTimeout(connectWebSocket, 5000);
        };
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setIsConnected(false);
        };
        
      } catch (err) {
        console.error('Failed to connect WebSocket:', err);
        setTimeout(connectWebSocket, 5000);
      }
    };
    
    connectWebSocket();
    
    // Cleanup on unmount
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, []);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((data: any) => {
    if (data.type === 'customer_health_update') {
      const healthUpdate = data.data;
      
      // Add notification for critical updates
      if (healthUpdate.intervention_priority === 'critical') {
        const notification = `⚠️ Critical alert: ${healthUpdate.customer_id} requires immediate intervention`;
        setNotifications(prev => [notification, ...prev.slice(0, 9)]); // Keep last 10
      }
      
      // Update at-risk customers if this customer is at risk
      if (healthUpdate.churn_probability > 0.5) {
        setAtRiskCustomers(prev => {
          const updated = prev.filter(c => c.customer_id !== healthUpdate.customer_id);
          return [{
            customer_id: healthUpdate.customer_id,
            company_name: healthUpdate.customer_id, // Would need company name from API
            last_health_score: healthUpdate.health_score,
            predicted_churn_score: healthUpdate.churn_probability,
            intervention_priority: healthUpdate.intervention_priority,
            risk_factors: [],
            last_updated: healthUpdate.last_updated
          }, ...updated];
        });
      }
      
      setLastUpdate(new Date());
    }
  }, []);

  // Load initial data
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Load KPIs and at-risk customers in parallel
      const [kpiResponse, atRiskResponse] = await Promise.all([
        fetch('/api/customer-success/kpis'),
        fetch('/api/customer-success/at-risk')
      ]);
      
      if (!kpiResponse.ok || !atRiskResponse.ok) {
        throw new Error('Failed to load dashboard data');
      }
      
      const kpiData = await kpiResponse.json();
      const atRiskData = await atRiskResponse.json();
      
      setKpis(kpiData);
      setAtRiskCustomers(atRiskData.at_risk_customers || []);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  const getHealthStatusColor = (status: string): string => {
    switch (status) {
      case 'excellent': return '#4caf50';
      case 'good': return '#8bc34a';
      case 'warning': return '#ff9800';
      case 'critical': return '#f44336';
      case 'churn_risk': return '#d32f2f';
      default: return '#9e9e9e';
    }
  };

  const getChurnRiskColor = (risk: string): string => {
    switch (risk) {
      case 'low': return '#4caf50';
      case 'medium': return '#ff9800';
      case 'high': return '#f44336';
      case 'critical': return '#d32f2f';
      default: return '#9e9e9e';
    }
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatPercentage = (value: number): string => {
    return `${value.toFixed(1)}%`;
  };

  // Health Score Gauge Component
  const HealthScoreGauge: React.FC<{ score: number; status: string }> = ({ score, status }) => {
    const gaugeData = {
      datasets: [{
        data: [score, 100 - score],
        backgroundColor: [getHealthStatusColor(status), '#f5f5f5'],
        borderWidth: 0
      }]
    };

    const gaugeOptions = {
      responsive: true,
      maintainAspectRatio: false,
      circumference: 180,
      rotation: 270,
      cutout: '75%',
      plugins: {
        legend: { display: false },
        tooltip: { enabled: false }
      }
    };

    return (
      <Box position="relative" height={200}>
        <Doughnut data={gaugeData} options={gaugeOptions} />
        <Box
          position="absolute"
          top="60%"
          left="50%"
          transform="translate(-50%, -50%)"
          textAlign="center"
        >
          <Typography variant="h3" fontWeight="bold" color={getHealthStatusColor(status)}>
            {score.toFixed(1)}
          </Typography>
          <Typography variant="caption" color="textSecondary">
            Health Score
          </Typography>
        </Box>
      </Box>
    );
  };

  // Health Distribution Chart
  const healthDistributionData = useMemo(() => {
    if (!kpis) return null;
    
    const distribution = kpis.distributions.health_status;
    
    return {
      labels: Object.keys(distribution).map(key => key.replace('_', ' ').toUpperCase()),
      datasets: [{
        data: Object.values(distribution),
        backgroundColor: Object.keys(distribution).map(status => getHealthStatusColor(status)),
        borderWidth: 2,
        borderColor: '#fff'
      }]
    };
  }, [kpis]);

  // Churn Risk Trends Chart
  const churnTrendData = useMemo(() => {
    if (!kpis) return null;
    
    // Generate sample trend data (in real app, this would come from API)
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    const churnRates = [4.2, 3.8, 4.5, 3.9, 3.2, 2.8];
    
    return {
      labels: months,
      datasets: [{
        label: 'Monthly Churn Rate (%)',
        data: churnRates,
        borderColor: '#f44336',
        backgroundColor: 'rgba(244, 67, 54, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }]
    };
  }, [kpis]);

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error" action={
          <Button color="inherit" size="small" onClick={refreshData}>
            Retry
          </Button>
        }>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Customer Success Dashboard
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Real-time customer health monitoring and churn prevention
          </Typography>
        </Box>
        
        <Box display="flex" gap={2} alignItems="center">
          {/* Connection Status */}
          <Chip
            icon={isConnected ? <CheckCircle /> : <Error />}
            label={isConnected ? 'Live' : 'Offline'}
            color={isConnected ? 'success' : 'error'}
            variant="outlined"
          />
          
          {/* Notifications */}
          <IconButton
            onClick={() => setShowNotifications(true)}
            color={notifications.length > 0 ? 'error' : 'default'}
          >
            <Badge badgeContent={notifications.length} color="error">
              <Notifications />
            </Badge>
          </IconButton>
          
          {/* Refresh Button */}
          <Button
            variant="outlined"
            startIcon={refreshing ? <Autorenew className="animate-spin" /> : <Refresh />}
            onClick={refreshData}
            disabled={refreshing}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Key Metrics Overview */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Customers
                  </Typography>
                  <Typography variant="h4">
                    {kpis?.overview.total_customers.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    {kpis?.overview.active_customers} active
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <People />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Avg Health Score
                  </Typography>
                  <Typography variant="h4">
                    {kpis?.health_metrics.avg_health_score.toFixed(1)}
                  </Typography>
                  <Typography variant="body2" color="info.main">
                    NPS: {kpis?.health_metrics.nps_score}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <Speed />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    At Risk Customers
                  </Typography>
                  <Typography variant="h4" color="warning.main">
                    {kpis?.overview.at_risk_customers}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Require intervention
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'warning.main' }}>
                  <Warning />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    LTV:CAC Ratio
                  </Typography>
                  <Typography variant="h4">
                    {kpis?.financial_metrics.ltv_cac_ratio.toFixed(1)}
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    Healthy ratio
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'info.main' }}>
                  <AttachMoney />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Health Distribution and Trends */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Customer Health Distribution
              </Typography>
              {healthDistributionData && (
                <Box height={300}>
                  <Doughnut
                    data={healthDistributionData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'bottom'
                        }
                      }
                    }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Churn Rate Trend
              </Typography>
              {churnTrendData && (
                <Box height={300}>
                  <Line
                    data={churnTrendData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        y: {
                          beginAtZero: true,
                          title: {
                            display: true,
                            text: 'Churn Rate (%)'
                          }
                        }
                      },
                      plugins: {
                        legend: {
                          display: false
                        }
                      }
                    }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* At-Risk Customers Table */}
      <Card mb={4}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              At-Risk Customers ({atRiskCustomers.length})
            </Typography>
            <Button
              startIcon={<FilterList />}
              variant="outlined"
              size="small"
            >
              Filter
            </Button>
          </Box>
          
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Company</TableCell>
                  <TableCell align="right">Health Score</TableCell>
                  <TableCell align="right">Churn Risk</TableCell>
                  <TableCell>Priority</TableCell>
                  <TableCell>Last Updated</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {atRiskCustomers.slice(0, 10).map((customer) => (
                  <TableRow key={customer.customer_id} hover>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Avatar sx={{ width: 32, height: 32 }}>
                          {customer.company_name.charAt(0)}
                        </Avatar>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {customer.company_name}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            {customer.customer_id}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Box display="flex" alignItems="center" justifyContent="flex-end" gap={1}>
                        <Typography variant="body2">
                          {customer.last_health_score.toFixed(1)}
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={customer.last_health_score}
                          sx={{ width: 60, height: 6, borderRadius: 3 }}
                          color={customer.last_health_score > 70 ? 'success' : 
                                 customer.last_health_score > 50 ? 'warning' : 'error'}
                        />
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {formatPercentage(customer.predicted_churn_score * 100)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={customer.intervention_priority.toUpperCase()}
                        size="small"
                        color={
                          customer.intervention_priority === 'critical' ? 'error' :
                          customer.intervention_priority === 'high' ? 'warning' :
                          customer.intervention_priority === 'medium' ? 'info' : 'default'
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {formatDistanceToNow(new Date(customer.last_updated), { addSuffix: true })}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Box display="flex" gap={1}>
                        <Tooltip title="Call Customer">
                          <IconButton size="small" color="primary">
                            <Phone fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Send Email">
                          <IconButton size="small" color="secondary">
                            <Email fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Create Task">
                          <IconButton size="small">
                            <Assignment fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          {atRiskCustomers.length > 10 && (
            <Box mt={2} textAlign="center">
              <Button variant="outlined">
                View All At-Risk Customers ({atRiskCustomers.length})
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Retention Metrics */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                30-Day Retention
              </Typography>
              <Typography variant="h3" color="success.main">
                {formatPercentage(kpis?.retention_rates.retention_30d || 0)}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                New customer retention
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                90-Day Retention
              </Typography>
              <Typography variant="h3" color="info.main">
                {formatPercentage(kpis?.retention_rates.retention_90d || 0)}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Quarterly retention
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                12-Month Retention
              </Typography>
              <Typography variant="h3" color="primary.main">
                {formatPercentage(kpis?.retention_rates.retention_12m || 0)}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Annual retention
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Notifications Drawer */}
      <Drawer
        anchor="right"
        open={showNotifications}
        onClose={() => setShowNotifications(false)}
      >
        <Box width={400} p={2}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Notifications</Typography>
            <IconButton onClick={() => setShowNotifications(false)}>
              <Close />
            </IconButton>
          </Box>
          
          <List>
            {notifications.length === 0 ? (
              <ListItem>
                <ListItemText
                  primary="No notifications"
                  secondary="You're all caught up!"
                />
              </ListItem>
            ) : (
              notifications.map((notification, index) => (
                <ListItem key={index} divider>
                  <ListItemIcon>
                    <Warning color="warning" />
                  </ListItemIcon>
                  <ListItemText
                    primary={notification}
                    secondary={formatDistanceToNow(new Date(), { addSuffix: true })}
                  />
                </ListItem>
              ))
            )}
          </List>
        </Box>
      </Drawer>

      {/* Floating Action Button for Quick Actions */}
      <Fab
        color="primary"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => {/* Open quick actions menu */}}
      >
        <Timeline />
      </Fab>

      {/* Last Update Indicator */}
      <Box
        position="fixed"
        bottom={16}
        left={16}
        bgcolor="background.paper"
        border={1}
        borderColor="divider"
        borderRadius={2}
        px={2}
        py={1}
      >
        <Typography variant="caption" color="textSecondary">
          Last updated: {format(lastUpdate, 'HH:mm:ss')}
        </Typography>
      </Box>
    </Container>
  );
};

export default CustomerSuccessDashboard;