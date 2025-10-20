
import React, { useEffect } from 'react';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useAppDispatch, useAppSelector } from '../hooks/redux';
import { fetchWorkOrders } from '../store/workOrdersSlice';
import { WorkOrder } from '../types/WorkOrder';

const columns: GridColDef[] = [
  { field: 'id', headerName: 'ID', width: 90 },
  { field: 'title', headerName: 'Title', width: 250 },
  { field: 'status', headerName: 'Status', width: 120 },
  { field: 'priority', headerName: 'Priority', width: 120 },
  { field: 'assignedTo', headerName: 'Assigned To', width: 180 },
  { field: 'dueDate', headerName: 'Due Date', width: 150 },
];

export const WorkOrderList: React.FC = () => {
  const dispatch = useAppDispatch();
  const { workOrders, loading } = useAppSelector(state => state.workOrders);

  useEffect(() => {
    dispatch(fetchWorkOrders());
  }, [dispatch]);

  return (
    <DataGrid
      rows={workOrders}
      columns={columns}
      loading={loading}
      checkboxSelection
      disableRowSelectionOnClick
      autoHeight
    />
  );
};
