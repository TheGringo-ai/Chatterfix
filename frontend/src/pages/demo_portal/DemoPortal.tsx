/**
 * 🧠 ChatterFix CMMS - Global Demo Hub
 * Centralized demo portal with automated tenant management
 * 
 * Features:
 * - Self-service demo environment creation
 * - Industry-specific guided tours
 * - Visitor tracking and behavior analytics
 * - Automated lead capture and nurturing
 * - Demo usage heatmaps and conversion optimization
 */

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import {
  Box,
  Container,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Avatar,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tab,
  Tabs,
  TabPanel
} from '@mui/material';
import {
  PlayArrow,
  Schedule,
  Group,
  TrendingUp,
  Security,
  DeviceHub,
  Analytics,
  Phone,
  Email,
  Business,
  ExpandMore,
  CheckCircle,
  Timeline,
  Dashboard,
  Settings,
  Mobile,
  Cloud,
  AutoAwesome
} from '@mui/icons-material';

interface DemoRequest {
  industry: string;
  companySize: string;
  role: string;
  useCase: string;
  firstName: string;
  lastName: string;
  email: string;
  company: string;
  phone?: string;
  region: string;
}

interface DemoTenant {
  tenantId: string;
  demoUrl: string;
  expiresAt: string;
  industry: string;
  sampleData: {
    assets: number;
    workOrders: number;
    users: number;
  };
  tourSteps: TourStep[];
}

interface TourStep {
  id: string;
  title: string;
  description: string;
  component: string;
  duration: number;
  completed: boolean;
}

interface AnalyticsData {
  totalVisitors: number;
  demoCreated: number;
  completionRate: number;
  averageSessionTime: number;
  topIndustries: { industry: string; count: number }[];
  conversionFunnel: { stage: string; count: number; rate: number }[];
}

const industryOptions = [
  { value: 'manufacturing', label: 'Manufacturing', icon: '🏭' },
  { value: 'healthcare', label: 'Healthcare', icon: '🏥' },
  { value: 'energy', label: 'Energy & Utilities', icon: '⚡' },
  { value: 'logistics', label: 'Logistics & Transportation', icon: '🚛' },
  { value: 'automotive', label: 'Automotive', icon: '🚗' },
  { value: 'aerospace', label: 'Aerospace & Defense', icon: '✈️' },
  { value: 'food_beverage', label: 'Food & Beverage', icon: '🍕' },
  { value: 'chemicals', label: 'Chemicals & Pharmaceuticals', icon: '🧪' },
  { value: 'other', label: 'Other', icon: '🏢' }
];

const companySizeOptions = [
  { value: 'startup', label: 'Startup (1-50 employees)' },
  { value: 'small', label: 'Small Business (51-200 employees)' },
  { value: 'medium', label: 'Medium Business (201-1000 employees)' },
  { value: 'large', label: 'Large Enterprise (1000+ employees)' },
  { value: 'enterprise', label: 'Fortune 500 Enterprise' }
];

const roleOptions = [
  { value: 'maintenance_manager', label: 'Maintenance Manager' },
  { value: 'facility_manager', label: 'Facility Manager' },
  { value: 'operations_director', label: 'Operations Director' },
  { value: 'plant_manager', label: 'Plant Manager' },
  { value: 'cto', label: 'CTO / Technical Executive' },
  { value: 'procurement', label: 'Procurement / Purchasing' },
  { value: 'consultant', label: 'Consultant / Systems Integrator' },
  { value: 'technician', label: 'Maintenance Technician' },
  { value: 'other', label: 'Other' }
];

const useCaseOptions = [
  { value: 'preventive_maintenance', label: 'Preventive Maintenance Scheduling' },
  { value: 'work_order_management', label: 'Work Order Management' },
  { value: 'asset_tracking', label: 'Asset Tracking & Management' },
  { value: 'inventory_management', label: 'Inventory & Parts Management' },
  { value: 'predictive_analytics', label: 'Predictive Analytics & AI' },
  { value: 'mobile_workforce', label: 'Mobile Workforce Management' },
  { value: 'compliance_reporting', label: 'Compliance & Reporting' },
  { value: 'cost_optimization', label: 'Cost Optimization & ROI' },
  { value: 'equipment_reliability', label: 'Equipment Reliability' }
];

const DemoPortal: React.FC = () => {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [demoRequest, setDemoRequest] = useState<DemoRequest>({
    industry: '',
    companySize: '',
    role: '',
    useCase: '',
    firstName: '',
    lastName: '',
    email: '',
    company: '',
    phone: '',
    region: 'us'
  });
  const [demoTenant, setDemoTenant] = useState<DemoTenant | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [showTourDialog, setShowTourDialog] = useState(false);
  const [tourProgress, setTourProgress] = useState(0);

  const steps = [
    'Industry & Role',
    'Contact Information', 
    'Demo Preferences',
    'Environment Setup'
  ];

  useEffect(() => {
    // Track page visit
    trackVisitorBehavior('demo_portal_visit', {
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      referrer: document.referrer
    });

    // Load analytics if admin
    loadAnalytics();
  }, []);

  const trackVisitorBehavior = async (event: string, data: any) => {
    try {
      await fetch('/api/demo/analytics/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event, data, timestamp: new Date().toISOString() })
      });
    } catch (error) {
      console.error('Error tracking behavior:', error);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await fetch('/api/demo/analytics');
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  const handleInputChange = (field: keyof DemoRequest, value: string) => {
    setDemoRequest(prev => ({
      ...prev,
      [field]: value
    }));

    // Track field interactions
    trackVisitorBehavior('form_field_change', {
      field,
      value: field === 'email' ? 'email_provided' : value,
      step: currentStep
    });
  };

  const validateStep = (step: number): boolean => {
    switch (step) {
      case 0:
        return !!(demoRequest.industry && demoRequest.companySize && demoRequest.role && demoRequest.useCase);
      case 1:
        return !!(demoRequest.firstName && demoRequest.lastName && demoRequest.email && demoRequest.company);
      case 2:
        return true; // Optional step
      default:
        return true;
    }
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => prev + 1);
      trackVisitorBehavior('demo_step_completed', {
        step: currentStep,
        stepName: steps[currentStep]
      });
    } else {
      setError('Please fill in all required fields');
    }
  };

  const handleBack = () => {
    setCurrentStep(prev => prev - 1);
  };

  const createDemoEnvironment = async () => {
    setLoading(true);
    setError(null);

    try {
      // Track demo creation attempt
      trackVisitorBehavior('demo_creation_started', demoRequest);

      const response = await fetch('/api/demo/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(demoRequest)
      });

      if (!response.ok) {
        throw new Error('Failed to create demo environment');
      }

      const tenant = await response.json();
      setDemoTenant(tenant);
      setCurrentStep(3);

      // Track successful demo creation
      trackVisitorBehavior('demo_created', {
        tenantId: tenant.tenantId,
        industry: demoRequest.industry,
        company: demoRequest.company
      });

      // Show guided tour option
      setTimeout(() => setShowTourDialog(true), 2000);

    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unknown error occurred');
      trackVisitorBehavior('demo_creation_failed', { error: error.toString() });
    } finally {
      setLoading(false);
    }
  };

  const startGuidedTour = async () => {
    if (!demoTenant) return;

    setShowTourDialog(false);
    setLoading(true);

    try {
      // Initialize guided tour
      const response = await fetch(`/api/demo/${demoTenant.tenantId}/tour/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          industry: demoRequest.industry,
          useCase: demoRequest.useCase
        })
      });

      if (response.ok) {
        const tourData = await response.json();
        trackVisitorBehavior('guided_tour_started', {
          tenantId: demoTenant.tenantId,
          tourSteps: tourData.steps.length
        });

        // Redirect to demo with tour overlay
        window.open(`${demoTenant.demoUrl}?tour=true&industry=${demoRequest.industry}`, '_blank');
      }
    } catch (error) {
      console.error('Error starting guided tour:', error);
    } finally {
      setLoading(false);
    }
  };

  const getIndustryTourSteps = (industry: string) => {
    const baseTourSteps = [
      {
        id: 'welcome',
        title: 'Welcome to ChatterFix CMMS',
        description: 'Get familiar with the main dashboard and navigation',
        component: 'Dashboard',
        duration: 60,
        completed: false
      },
      {
        id: 'assets',
        title: 'Asset Management',
        description: 'View and manage your equipment and assets',
        component: 'AssetList',
        duration: 90,
        completed: false
      },
      {
        id: 'work_orders',
        title: 'Work Order Management',
        description: 'Create, assign, and track maintenance work orders',
        component: 'WorkOrderList',
        duration: 120,
        completed: false
      }
    ];

    // Industry-specific tour steps
    const industrySteps = {
      manufacturing: [
        {
          id: 'production_line',
          title: 'Production Line Monitoring',
          description: 'Monitor production equipment in real-time',
          component: 'ProductionDashboard',
          duration: 90,
          completed: false
        },
        {
          id: 'predictive_maintenance',
          title: 'Predictive Maintenance AI',
          description: 'See AI predictions for equipment failures',
          component: 'PredictiveAnalytics',
          duration: 120,
          completed: false
        }
      ],
      healthcare: [
        {
          id: 'biomedical_equipment',
          title: 'Biomedical Equipment Tracking',
          description: 'Manage critical healthcare equipment',
          component: 'BiomedicalAssets',
          duration: 90,
          completed: false
        },
        {
          id: 'compliance_reporting',
          title: 'Compliance & Reporting',
          description: 'Generate regulatory compliance reports',
          component: 'ComplianceReports',
          duration: 100,
          completed: false
        }
      ],
      energy: [
        {
          id: 'energy_monitoring',
          title: 'Energy Asset Monitoring',
          description: 'Monitor power generation and distribution equipment',
          component: 'EnergyDashboard',
          duration: 90,
          completed: false
        },
        {
          id: 'safety_compliance',
          title: 'Safety & Environmental Compliance',
          description: 'Track safety incidents and environmental metrics',
          component: 'SafetyDashboard',
          duration: 100,
          completed: false
        }
      ]
    };

    return [...baseTourSteps, ...(industrySteps[industry] || [])];
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Industry</InputLabel>
                <Select
                  value={demoRequest.industry}
                  onChange={(e) => handleInputChange('industry', e.target.value)}
                  required
                >
                  {industryOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <span>{option.icon}</span>
                        {option.label}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Company Size</InputLabel>
                <Select
                  value={demoRequest.companySize}
                  onChange={(e) => handleInputChange('companySize', e.target.value)}
                  required
                >
                  {companySizeOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Your Role</InputLabel>
                <Select
                  value={demoRequest.role}
                  onChange={(e) => handleInputChange('role', e.target.value)}
                  required
                >
                  {roleOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Primary Use Case</InputLabel>
                <Select
                  value={demoRequest.useCase}
                  onChange={(e) => handleInputChange('useCase', e.target.value)}
                  required
                >
                  {useCaseOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        );

      case 1:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="First Name"
                value={demoRequest.firstName}
                onChange={(e) => handleInputChange('firstName', e.target.value)}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Last Name"
                value={demoRequest.lastName}
                onChange={(e) => handleInputChange('lastName', e.target.value)}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Business Email"
                type="email"
                value={demoRequest.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Company Name"
                value={demoRequest.company}
                onChange={(e) => handleInputChange('company', e.target.value)}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Phone Number (Optional)"
                value={demoRequest.phone}
                onChange={(e) => handleInputChange('phone', e.target.value)}
              />
            </Grid>
          </Grid>
        );

      case 2:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Demo Preferences
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="body1" gutterBottom>
                  Based on your selections, we'll create a customized demo environment with:
                </Typography>
                <Box mt={2}>
                  {demoRequest.industry && (
                    <Chip
                      icon={<Business />}
                      label={`${industryOptions.find(i => i.value === demoRequest.industry)?.label} Industry Data`}
                      color="primary"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  )}
                  {demoRequest.useCase && (
                    <Chip
                      icon={<Settings />}
                      label={useCaseOptions.find(u => u.value === demoRequest.useCase)?.label}
                      color="secondary"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  )}
                  <Chip
                    icon={<AutoAwesome />}
                    label="AI-Powered Insights"
                    color="success"
                    sx={{ mr: 1, mb: 1 }}
                  />
                  <Chip
                    icon={<Mobile />}
                    label="Mobile App Access"
                    color="info"
                    sx={{ mr: 1, mb: 1 }}
                  />
                </Box>
              </Grid>
              <Grid item xs={12}>
                <Alert severity="info">
                  Your demo environment will be available for 14 days with full access to all ChatterFix features.
                  Our team will follow up to answer any questions and discuss your specific requirements.
                </Alert>
              </Grid>
            </Grid>
          </Box>
        );

      case 3:
        return demoTenant ? (
          <Box textAlign="center">
            <CheckCircle color="success" sx={{ fontSize: 80, mb: 2 }} />
            <Typography variant="h4" gutterBottom>
              Your Demo is Ready!
            </Typography>
            <Typography variant="body1" paragraph>
              We've created a customized ChatterFix CMMS environment with {demoRequest.industry} industry data.
              Your demo includes {demoTenant.sampleData.assets} assets, {demoTenant.sampleData.workOrders} work orders,
              and {demoTenant.sampleData.users} sample users.
            </Typography>
            
            <Grid container spacing={2} justifyContent="center" sx={{ mt: 3 }}>
              <Grid item>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<PlayArrow />}
                  onClick={() => window.open(demoTenant.demoUrl, '_blank')}
                >
                  Launch Demo
                </Button>
              </Grid>
              <Grid item>
                <Button
                  variant="outlined"
                  size="large"
                  startIcon={<Timeline />}
                  onClick={() => setShowTourDialog(true)}
                >
                  Start Guided Tour
                </Button>
              </Grid>
            </Grid>

            <Box mt={4}>
              <Typography variant="h6" gutterBottom>
                What's Next?
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Email color="primary" sx={{ fontSize: 40, mb: 1 }} />
                      <Typography variant="h6">Check Your Email</Typography>
                      <Typography variant="body2">
                        Demo credentials and quick start guide sent to {demoRequest.email}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Schedule color="secondary" sx={{ fontSize: 40, mb: 1 }} />
                      <Typography variant="h6">Book a Consultation</Typography>
                      <Typography variant="body2">
                        Schedule a 30-minute call with our CMMS experts
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Group color="success" sx={{ fontSize: 40, mb: 1 }} />
                      <Typography variant="h6">Join Community</Typography>
                      <Typography variant="body2">
                        Connect with other maintenance professionals
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Box>

            <Alert severity="warning" sx={{ mt: 3 }}>
              Demo expires on {new Date(demoTenant.expiresAt).toLocaleDateString()}. 
              Contact us to extend or convert to a full license.
            </Alert>
          </Box>
        ) : null;

      default:
        return null;
    }
  };

  const renderAnalyticsDashboard = () => {
    if (!analytics) return <CircularProgress />;

    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Demo Portal Analytics
        </Typography>
        
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Visitors
                </Typography>
                <Typography variant="h4">
                  {analytics.totalVisitors.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Demos Created
                </Typography>
                <Typography variant="h4">
                  {analytics.demoCreated.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Completion Rate
                </Typography>
                <Typography variant="h4">
                  {analytics.completionRate.toFixed(1)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Avg Session Time
                </Typography>
                <Typography variant="h4">
                  {Math.round(analytics.averageSessionTime / 60)}m
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Top Industries
                </Typography>
                {analytics.topIndustries.map((item, index) => (
                  <Box key={item.industry} display="flex" justifyContent="space-between" mb={1}>
                    <Typography>{item.industry}</Typography>
                    <Typography fontWeight="bold">{item.count}</Typography>
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Conversion Funnel
                </Typography>
                {analytics.conversionFunnel.map((stage, index) => (
                  <Box key={stage.stage} mb={2}>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography>{stage.stage}</Typography>
                      <Typography>{stage.count} ({stage.rate.toFixed(1)}%)</Typography>
                    </Box>
                    <LinearProgress variant="determinate" value={stage.rate} />
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box textAlign="center" mb={6}>
        <Typography variant="h2" gutterBottom>
          Experience ChatterFix CMMS
        </Typography>
        <Typography variant="h5" color="textSecondary" paragraph>
          Get instant access to a personalized demo environment
        </Typography>
        <Box display="flex" justifyContent="center" gap={2} flexWrap="wrap">
          <Chip icon={<Cloud />} label="Cloud-Based" color="primary" />
          <Chip icon={<Mobile />} label="Mobile-First" color="secondary" />
          <Chip icon={<AutoAwesome />} label="AI-Powered" color="success" />
          <Chip icon={<Security />} label="Enterprise Security" color="info" />
        </Box>
      </Box>

      {/* Demo Creation Flow */}
      {!demoTenant && (
        <Card sx={{ maxWidth: 800, mx: 'auto', mb: 4 }}>
          <CardContent sx={{ p: 4 }}>
            <Stepper activeStep={currentStep} alternativeLabel sx={{ mb: 4 }}>
              {steps.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>

            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            )}

            {renderStepContent(currentStep)}

            <Box display="flex" justifyContent="space-between" mt={4}>
              <Button
                disabled={currentStep === 0}
                onClick={handleBack}
              >
                Back
              </Button>
              
              {currentStep === steps.length - 1 ? (
                <Button
                  variant="contained"
                  onClick={createDemoEnvironment}
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <PlayArrow />}
                >
                  {loading ? 'Creating Demo...' : 'Create My Demo'}
                </Button>
              ) : (
                <Button
                  variant="contained"
                  onClick={handleNext}
                  disabled={!validateStep(currentStep)}
                >
                  Next
                </Button>
              )}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Demo Environment Ready */}
      {demoTenant && (
        <Card sx={{ maxWidth: 1000, mx: 'auto' }}>
          <CardContent sx={{ p: 4 }}>
            {renderStepContent(3)}
          </CardContent>
        </Card>
      )}

      {/* Guided Tour Dialog */}
      <Dialog open={showTourDialog} onClose={() => setShowTourDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <Timeline />
            Guided Tour Available
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography paragraph>
            Would you like to take a guided tour of ChatterFix CMMS? We'll walk you through the key features
            relevant to your {demoRequest.industry} industry and {demoRequest.useCase} use case.
          </Typography>
          
          <Typography variant="h6" gutterBottom>
            Tour includes:
          </Typography>
          <Box component="ul" sx={{ pl: 2 }}>
            {getIndustryTourSteps(demoRequest.industry).map((step) => (
              <li key={step.id}>
                <Typography>
                  {step.title} - {step.description} ({step.duration}s)
                </Typography>
              </li>
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowTourDialog(false)}>
            Skip Tour
          </Button>
          <Button variant="contained" onClick={startGuidedTour} disabled={loading}>
            Start Guided Tour
          </Button>
        </DialogActions>
      </Dialog>

      {/* Feature Highlights */}
      <Box mt={8}>
        <Typography variant="h4" textAlign="center" gutterBottom>
          Why ChatterFix CMMS?
        </Typography>
        <Grid container spacing={4} sx={{ mt: 2 }}>
          <Grid item xs={12} md={3}>
            <Card sx={{ height: '100%', textAlign: 'center' }}>
              <CardContent>
                <TrendingUp sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  40% Downtime Reduction
                </Typography>
                <Typography variant="body2">
                  AI-powered predictive maintenance prevents failures before they happen
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card sx={{ height: '100%', textAlign: 'center' }}>
              <CardContent>
                <Mobile sx={{ fontSize: 60, color: 'secondary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Mobile-First Design
                </Typography>
                <Typography variant="body2">
                  Native iOS and Android apps for technicians in the field
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card sx={{ height: '100%', textAlign: 'center' }}>
              <CardContent>
                <Analytics sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Real-Time Analytics
                </Typography>
                <Typography variant="body2">
                  Live dashboards with actionable insights and KPI tracking
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card sx={{ height: '100%', textAlign: 'center' }}>
              <CardContent>
                <Security sx={{ fontSize: 60, color: 'info.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Enterprise Security
                </Typography>
                <Typography variant="body2">
                  SOC2, HIPAA compliance with OAuth2 and zero-trust architecture
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* FAQ Section */}
      <Box mt={8}>
        <Typography variant="h4" textAlign="center" gutterBottom>
          Frequently Asked Questions
        </Typography>
        <Box maxWidth={800} mx="auto" mt={4}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="h6">How long does the demo last?</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography>
                Your demo environment is available for 14 days with full access to all ChatterFix features.
                You can extend the demo period by contacting our sales team.
              </Typography>
            </AccordionDetails>
          </Accordion>
          
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="h6">Is my data secure in the demo?</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography>
                Demo environments use sample data and are automatically destroyed after expiration.
                All demo instances are isolated and encrypted with enterprise-grade security.
              </Typography>
            </AccordionDetails>
          </Accordion>
          
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="h6">Can I import my own data?</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography>
                Demo environments come pre-loaded with industry-specific sample data.
                For testing with your own data, we can set up a pilot environment with our sales team.
              </Typography>
            </AccordionDetails>
          </Accordion>
        </Box>
      </Box>
    </Container>
  );
};

export default DemoPortal;