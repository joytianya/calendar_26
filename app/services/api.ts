// 设置跳过时间段
setSkipPeriod: async (data: SkipPeriodCreate): Promise<SkipPeriod> => {
  console.log('API调用 - 设置跳过时间段，发送数据:', JSON.stringify(data));
  
  // 确保日期字段是纯日期字符串，不包含时间部分
  let requestData = { ...data };
  if (typeof data.date === 'string' && data.date.length === 10) {
    // 如果是纯日期字符串 (YYYY-MM-DD)，不做修改
    console.log('API调用 - 使用纯日期字符串:', data.date);
  } else if (typeof data.date === 'string' && data.date.includes('T')) {
    // 如果包含时间部分，只取日期部分
    requestData.date = data.date.split('T')[0];
    console.log('API调用 - 提取ISO日期字符串中的日期部分:', requestData.date);
  }
  
  console.log('API调用 - 最终发送数据:', JSON.stringify(requestData));
  const response = await api.post<SkipPeriod>('/calendar/skip-period', requestData);
  return response.data;
}, 