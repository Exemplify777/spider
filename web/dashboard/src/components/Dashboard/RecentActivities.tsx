import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Divider } from '@mui/material';

interface RecentActivitiesProps {
  activities: any[];
}

const RecentActivities: React.FC<RecentActivitiesProps> = ({ activities }) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Recent Activities
        </Typography>
        {activities.length > 0 ? (
          <List dense>
            {activities.map((activity, index) => (
              <React.Fragment key={index}>
                <ListItem>
                  <ListItemText
                    primary={activity.message || activity.action}
                    secondary={activity.timestamp ? new Date(activity.timestamp).toLocaleString() : ''}
                  />
                </ListItem>
                {index < activities.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="textSecondary">
            No recent activities
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default RecentActivities;
