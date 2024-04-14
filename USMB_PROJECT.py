#USMB PROJECT
#%%
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#%%
folderpath = r"C:\Users\mpaul\Downloads\DataTwenteDay3Try1"

#%%
#ORGANIZE THE DATA IN DICTIONARIES

def organize_dict(folder_path):
    waterday3 = {}

    count = 0
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # Extract information from the file name
            parts = file.split('_')
            if len(parts) == 6:
                voltage, _, _, file_type, volt_range, _ = parts  # Include range in splitting
                if volt_range == '50mV':
                    mintime = 20e-6
                    maxtime = 90e-6
                elif volt_range == '100mV':
                    mintime = 30e-6
                    maxtime = 90e-6
                elif volt_range == '200mV':
                    mintime = 30e-6
                    maxtime = 90e-6
            elif len(parts) == 5: #If range is not included in the name of the file, set manually
                voltage, _, _, file_type, _ = parts 
                if voltage == '0.2V': 
                    volt_range = '50mV'
                    mintime = 20e-6
                    maxtime = 90e-6
                elif voltage == '0.4V':
                    volt_range = '50mV'
                    mintime = 20e-6
                    maxtime = 90e-6
                elif voltage == '0.6V':
                    volt_range = '100mV'
                    mintime = 30e-6
                    maxtime = 90e-6
                elif  voltage == '0.9V':
                    volt_range = '200mV'
                    mintime = 30e-6
                    maxtime = 90e-6
                elif voltage == '1.2V':
                    volt_range = '200mV'
                    mintime = 30e-6
                    maxtime = 90e-6

            else:
                continue 

            # Initialize dictionaries if not present
            if voltage not in waterday3:
                waterday3[voltage] = {}
            if file_type not in waterday3[voltage]:
                waterday3[voltage][file_type] = {}
            
            # Add additional voltage levels as keys, 
            """IMPORTANT"""
            # here the volt_range was put before the time domain and frequency domain info
            # as I found it easier, but I guess by just switching them it should do
            if volt_range not in waterday3[voltage][file_type]:
                waterday3[voltage][file_type][volt_range] = {'td': [], 'fd': []}


            # Read CSV file and process data
            file_df = pd.read_csv(os.path.join(root, file), sep=';', skiprows=[1], usecols=['Time', 'Channel C'], decimal=',')
            # Keep only the information from 35 to 90 us
            file_df['Time'] = pd.to_numeric(file_df['Time'], errors='coerce', downcast='float')
            file_df['Channel C'] = pd.to_numeric(file_df['Channel C'], errors='coerce', downcast='float')
            
            # Convert 'Time' column to microseconds
            file_df['Time'] *= 1e-6

            # Keep only the information from 35 to 90 us
            """COMMENT TO CHECK WHAT TIME RANGE TO CHOOSE!!!
            SELECTED TIME FRAMES (us):

            0.2V: 20-90
            0.4V: 30-95
            0.6V: 30-90
            0.9V: ALREADY CHOSEN
            1.2V: 30-90

            """
            mintime = 30e-6
            maxtime = 90e-6
            ini = file_df['Time'] > mintime
            fini = file_df['Time'] < maxtime
            file_df_filtered = file_df[ini&fini]
            file_df = file_df_filtered
            file_df.reset_index(drop=True, inplace=True)
            
            offset = file_df['Channel C'].mean()
            file_df['Offset'] = offset 
            file_df['Channel C Corrected'] = file_df['Channel C'] - offset

            dt = file_df['Time'].diff().mean()
            #Generate an arrange of frequencies
            frfft = np.linspace(0, 1/dt, len(file_df))
            #Apply the fourier transform
            TF = 2 * np.abs(np.fft.fft(file_df['Channel C Corrected'])) / len(file_df)



            # Append data to dictionary
            waterday3[voltage][file_type][volt_range]['td'].append(file_df)

            # Create DataFrame for frequency domain data
            fourier_df = pd.DataFrame({'Frequency': frfft, 'Amplitude': TF})
            
            positive_freq_mask = fourier_df['Frequency'] < 10e6
            fourier_df = fourier_df[positive_freq_mask]
            
            # Append Fourier data to dictionary
            waterday3[voltage][file_type][volt_range]['fd'].append(fourier_df)
        # count = count+1

    return waterday3
# %%
#APPLY THE ORGANIZATION
whole_dict = organize_dict(folderpath)


#%%
#PLOT IN THE TIME DOMAIN

#Extract the correct voltage ranges for the corresponding voltages
voltage_to_range = {
    '0.2V': '50mV',
    '0.4V': '50mV',
    '0.6V': '100mV',
    '0.9V': '200mV',
    '1.2V': '200mV',
}

voltagecomplete = ['0.2V', '0.4V', '0.6V', '0.9V','1.2V']

fig, axs = plt.subplots(5, 3, figsize=(15, 20))

for i, volt in enumerate(voltagecomplete):
    volt_range = voltage_to_range.get(volt, '')
    for j in range(3):
        random_voltage = whole_dict[volt]['noMB'][volt_range]['td'][j]
        random_volt_time = random_voltage['Time'] *1e5
        # Plot random_voltage
        axs[i, j].plot(random_volt_time, random_voltage['Channel C'])
        axs[i,j].locator_params(axis='x', nbins = 30)
        axs[i, j].set_title(f'Voltage - {volt} - {j}')
        axs[i, j].set_xlabel('Time (10-5 s)')
        axs[i, j].set_ylabel('Amplitude (mV)')
        axs[i,j].grid(True)

plt.tight_layout()

plt.show()

# %%
#CALCULATE THE MEAN OF THE 3 FOURIER SPECTRA

def fouriermean(replicalist):
    meanlist = []
    for i in range(len(replicalist[0])):
        meanlist.append((replicalist[0]['Amplitude'][i] +  replicalist[1]['Amplitude'][i] + replicalist[2]['Amplitude'][i]) /3)
    
    meanfourier_df = pd.DataFrame({'Frequency': replicalist[0]['Frequency'], 'Amplitude': meanlist})

    # plt.figure(figsize=(10, 6))
    # plt.plot(meanfourier_df['Frequency'], meanfourier_df['Amplitude'], color='blue')
    # plt.title('Mean fourier Domain')
    # plt.xlabel('Frequency (MHz)')
    # plt.ylabel('Amplitude (mV)')
    # plt.grid(True)
    # plt.xlim(0, 15)
    # plt.show()

    return meanfourier_df

#%%
#CALCULATE THE MEAN OF 2 FOURIER SPECTRA FOR THE 0.4V SAMPLES AS ONE OF THE SAMPLES WAS CORRUPTED
def fouriermean04(replicalist):
    meanlist = []
    for i in range(len(replicalist[0])):
        meanlist.append((replicalist[1]['Amplitude'][i] + replicalist[2]['Amplitude'][i]) /2)

    meanfourier_df = pd.DataFrame({'Frequency': replicalist[0]['Frequency'], 'Amplitude': meanlist})

    return meanfourier_df

#%%
#SEPARATE CALCULATION OF THE MEAN FOR THE 0V MEASUREMENTS AS WE HAVE DIFFERENT RANGES
for vr in ['50mV', '100mV', '200mV']: 
    new_list1 = whole_dict['0.0V']['noMB'][vr]['fd']
    mean_list1 = fouriermean(new_list1)   
    whole_dict['0.0V']['noMB'][vr]['fd'].append(mean_list1)

#%%
#Extract the correct voltage ranges for the corresponding voltages
voltage_to_range = {
    '0.2V': '50mV',
    '0.4V': '50mV',
    '0.6V': '100mV',
    '0.9V': '200mV',
    '1.2V': '200mV',
}

#%%
#The corresponding voltages to loop through
voltage = ['0.2V', '0.6V', '0.9V', '1.2V'] 

# Calculate the mean of the 3 triplicates for the MB
for volt in voltage:
    volt_range = voltage_to_range.get(volt, '')
    new_list = whole_dict[volt]['MB'][volt_range]['fd']
    mean_list = fouriermean(new_list) 
    whole_dict[volt]['MB'][volt_range]['fd'].append(mean_list)

    
#MEAN VALUE FOR THE 0.4V SAMPLES

new_list04 = whole_dict['0.4V']['MB']['50mV']['fd']
mean_list04 = fouriermean04(new_list04) 
whole_dict['0.4V']['MB']['50mV']['fd'].append(mean_list04)


# Calculate the mean of the 3 triplicates for the noMB
for volt in voltage:
    volt_range = voltage_to_range.get(volt, '')
    new_list = whole_dict[volt]['noMB'][volt_range]['fd']
    mean_list = fouriermean(new_list)   
    whole_dict[volt]['noMB'][volt_range]['fd'].append(mean_list)

#SAME FOR noMB 0.4V noMB

new_list04noMB = whole_dict['0.4V']['noMB']['50mV']['fd']
mean_list04noMB = fouriermean04(new_list04noMB) 
whole_dict['0.4V']['noMB']['50mV']['fd'].append(mean_list04noMB)

#%%

voltagecomplete = ['0.2V', '0.4V', '0.6V', '0.9V', '1.2V'] 


#%%
# volt_range = voltage_to_range.get('0.6V', '')
# random_voltage = whole_dict['0.6V']['noMB'][volt_range]['fd'][3]
# # random_voltage['Amplitude'] = 20* np.log10(abs(random_voltage['Amplitude']))
# # print(random_voltage)
# random_ref = whole_dict['0.0V']['noMB'][volt_range]['fd'][3]
# # random_ref['Amplitude'] = 20* np.log10(abs(random_ref['Amplitude']))

# # Plot random_voltage
# plt.plot(random_voltage['Frequency'], random_voltage['Amplitude'])
# plt.title(f'Voltage - 0.6V', fontsize= 30)
# plt.xlim(0, 10*1e6)
# plt.xlabel('Frequency (Hz)', fontsize = 25)
# plt.ylabel('Amplitude (mV)', fontsize = 25)
# plt.xticks(fontsize=25)
# plt.yticks(fontsize=25)
# plt.show()

# #%%
# plt.plot(random_ref['Frequency'], random_ref['Amplitude'])
# plt.title(f'Voltage - 0.0V 100mV', fontsize= 30)
# plt.xlim(0, 10*1e6)
# plt.xlabel('Frequency (Hz)', fontsize = 25)
# plt.ylabel('Amplitude (mV)', fontsize = 25)
# plt.xticks(fontsize=25)
# plt.yticks(fontsize=25)
# plt.show()


#%%
#PLOT IN FREQUENCY DOMAIN AGAINST THE 0V REFERENCE

fig, axs = plt.subplots(5, 3, figsize=(15, 20))

for i, volt in enumerate(voltagecomplete):
    volt_range = voltage_to_range.get(volt, '')
    random_voltage = whole_dict[volt]['noMB'][volt_range]['fd'][3]
    random_ref = whole_dict['0.0V']['noMB'][volt_range]['fd'][3]

    # Plot random_voltage
    axs[i, 0].plot(random_voltage['Frequency'], random_voltage['Amplitude'])
    axs[i, 0].set_title(f'Voltage - {volt}')
    axs[i, 0].set_xlim(0, 10*1e6)
    axs[i, 0].set_xlabel('Frequency (Hz)')
    axs[i, 0].set_ylabel('Amplitude (mV)')

    # Plot random_ref
    axs[i, 1].plot(random_ref['Frequency'], random_ref['Amplitude'])
    axs[i, 1].set_title(f'Reference - 0.0V')
    axs[i, 1].set_xlim(0, 10*1e6)
    axs[i, 1].set_xlabel('Frequency (Hz)')
    axs[i, 1].set_ylabel('Amplitude (mV)')

    # Plot overlay
    axs[i, 2].plot(random_voltage['Frequency'], random_voltage['Amplitude'], label='Voltage')
    axs[i, 2].plot(random_ref['Frequency'], random_ref['Amplitude'], label='Reference')
    axs[i, 2].set_title(f'Overlay - {volt}')
    axs[i, 2].set_xlim(0, 10*1e6)
    axs[i, 2].set_xlabel('Frequency (Hz)')
    axs[i, 2].set_ylabel('Amplitude (mV)')
    axs[i, 2].legend()


plt.tight_layout()
plt.show()

# %%
auc_total = []

#%%
"""BE AWARE: HERE WE REDEFINED THE WHOLE DICT OF THE REFERENCES TO BE IN DB SCALE HERE"""

for vr in ['50mV', '100mV', '200mV']:
    random_ref1 = whole_dict['0.0V']['noMB'][vr]['fd'][3]
    whole_dict['0.0V']['noMB'][vr]['fd'][3]['Amplitude'] = 20* np.log10(random_ref1['Amplitude']/1)

#%%
# We use the range to select the corresponding 0V data and perform the subtraction
for volt1 in voltagecomplete:
    random_ref = pd.DataFrame()
    volt_range1 = voltage_to_range.get(volt1, '')
    random_voltage = whole_dict[volt1]['MB'][volt_range1]['fd'][3]
    random_voltage['Amplitude'] = 20* np.log10(random_voltage['Amplitude']/1)
    random_ref = whole_dict['0.0V']['noMB'][volt_range1]['fd'][3]
    
    subtraction_array = random_voltage['Amplitude'] - random_ref['Amplitude']
    
    #Integration of the subtraction to get the BBN
    abc = 0.0
    for dBvalue in subtraction_array:
        abc += dBvalue*20000
    auc_total.append(abc)


plt.figure(figsize=(8, 6))

plt.plot(voltagecomplete, auc_total, marker='o', linestyle='-', color='b', label='ABC Total')
plt.xlabel('Voltage')
plt.ylabel('BBN (dB*Hz)')
plt.title('BBN vs. Voltage')
plt.grid(True)
plt.legend()

plt.show()  # Display the plot

#%%
#PLOTS, THIS IS ALREADY IN dB SCALE
fig, axs = plt.subplots(5, 3, figsize=(15, 20))

for i, volt in enumerate(voltagecomplete):
    volt_range = voltage_to_range.get(volt, '')
    print(volt_range)
    random_voltage = whole_dict[volt]['MB'][volt_range]['fd'][3]
    random_ref = whole_dict['0.0V']['noMB'][volt_range]['fd'][3]

    # Plot random_voltage
    axs[i, 0].plot(whole_dict[volt]['MB'][volt_range]['fd'][3]['Frequency'], random_voltage['Amplitude'])
    axs[i, 0].set_title(f'Voltage - {volt}')
    axs[i, 0].set_xlim(0, 10*1e6)
    axs[i, 0].set_ylim(-50, 25)
    axs[i, 0].set_xlabel('Frequency (Hz)')
    axs[i, 0].set_ylabel('Amplitude (dB)')

    # Plot random_ref
    axs[i, 1].plot(random_ref['Frequency'], random_ref['Amplitude'])
    axs[i, 1].set_title(f'Reference - 0.0V')
    axs[i, 1].set_xlim(0, 10*1e6)
    axs[i, 1].set_ylim(-50, 25)
    axs[i, 1].set_xlabel('Frequency (Hz)')
    axs[i, 1].set_ylabel('Amplitude (dB)')

    # Plot overlay
    axs[i, 2].plot(random_voltage['Frequency'], random_voltage['Amplitude'], label='Voltage')
    axs[i, 2].plot(random_ref['Frequency'], random_ref['Amplitude'], label='Reference')
    axs[i, 2].set_title(f'Overlay - {volt}')
    axs[i, 2].set_xlim(0, 10*1e6)
    axs[i, 2].set_ylim(-50, 25)
    axs[i, 2].set_xlabel('Frequency (Hz)')
    axs[i, 2].set_ylabel('Amplitude (dB)')
    axs[i, 2].legend()


plt.tight_layout()
plt.show()

#%%
# We use the range to select the corresponding 0V data and perform the subtraction
frequencies_sub = [1.125e+06]
frequencies_fund = [2.25e+06]

def plot_me(freq):
    auc_pressures = []
    for i, volt1 in enumerate(voltagecomplete):
        #subtraction_array = []
        random_ref = pd.DataFrame()
        #print(volt1)
        volt_range1 = voltage_to_range.get(volt1, '')
        random_voltage = whole_dict[volt1]['MB'][volt_range1]['fd'][3]
        random_ref = whole_dict['0.0V']['noMB'][volt_range1]['fd'][3]

        #print(random_voltage['Amplitude'])
        for frequency in freq:
            mintime = frequency - 0.05e+06
            maxtime = frequency + 0.05e+06
            ini = random_voltage['Frequency'] > mintime
            fini = random_voltage['Frequency'] < maxtime
            inir = random_ref['Frequency'] > mintime
            finir = random_ref['Frequency'] < maxtime
            file_df_filtered_p = random_voltage[ini&fini]
            file_df_filtered_r = random_ref[inir&finir]
            random_voltage = file_df_filtered_p
            random_voltage.reset_index(drop=True, inplace=True)
            random_ref = file_df_filtered_r
            random_ref.reset_index(drop=True, inplace=True)

            subtraction_array = random_voltage['Amplitude'] - random_ref['Amplitude']

            #Integration of the subtraction to get the BBN
            abc = 0.0
            for dBvalue in subtraction_array:
                abc += dBvalue*20000
            auc_pressures.append(abc/auc_total[i])
    return auc_pressures

#%%
plot_data_sub = plot_me(frequencies_sub)
plot_data_fund = plot_me(frequencies_fund)

plt.figure(figsize=(8, 6))

plt.plot(voltagecomplete, plot_data_sub, marker='o', linestyle='-', color='b', label='Subharmonic')
plt.plot(voltagecomplete, plot_data_fund, marker='v', linestyle='-', color='r', label='Fundamental')

plt.xlabel('Voltage')
plt.ylabel('Content (dB*Hz)')
plt.title('Fundamental & Subharmonic Content vs. Voltage')
plt.grid(True)
plt.legend()


plt.show()  # Display the plot

