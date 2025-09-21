from playwright.async_api import Page

class DeviceManager:
    def __init__(self, page : Page):
        self.page = page
        self.devices = {}
        self._name_counter = {}

    async def d_count(self):
        page = self.page
        self.devices = {}
        # If waterfall-grid__column on the page - then medium size, if it isn't then small size. At least its working now.
        if await page.locator("xpath=//div[@class='waterfall-grid__column']").count():
            #  Finding visible cards which have text
            devices_cards = await page.locator("//div[contains(@class, 'card-item-small')]").filter(
                has=page.locator(
                    "xpath=//div[@class='typography typography_align_center typography_color_primary typography_multi-line-clamp card-item-device-medium__text typography_header-16-m' and normalize-space(text()) != '']"
                )).filter(visible=True).all()
        else:
            devices_cards = await page.locator("//div[contains(@class, 'card-item-small')]").filter(
                has=page.locator(
                    "xpath=//div[@class='typography typography_align_inherit typography_color_primary typography_single-line-clamp card-item-device-small__text typography_text-13-m' and normalize-space(text()) != '']"
                )).filter(visible=True).all()
        # Finding visible cards which have switch
        activatable_devices_cards = await page.locator("//div[contains(@class, 'card-item-small')]").filter(
            has=page.locator(
                "xpath=//div[@class='typography typography_align_inherit typography_color_primary typography_single-line-clamp card-item-device-small__text typography_text-13-m' and normalize-space(text()) != '']"
            )).filter(has=page.locator("xpath=//div[contains(@aria-label,'ключить')]")).filter(visible=True).all()
        # Splitting cards on names, locations and states
        for activatable_devices_card in activatable_devices_cards:
            activatable_device_info = (await activatable_devices_card.inner_text()).splitlines()
            activatable_device_name = activatable_device_info[0]
            activatable_device_place = activatable_device_info[1] if len(activatable_device_info) > 1 else ""
            activatable_device_button = activatable_devices_card.locator(
                "xpath=//div[contains(@aria-label, 'ключить')]")
            activatable_device_button_state = await activatable_device_button.get_attribute('aria-label')
            activatable_device_state = False if activatable_device_button_state == 'Включить' else True
            if activatable_device_name in self.devices:
                self._name_counter[activatable_device_name] +=1
                activatable_device_name = activatable_device_name + f" ({str(self._name_counter[activatable_device_name])})"
            else:
                self._name_counter[activatable_device_name] = 1
            self.devices[activatable_device_name] = (Device(activatable_device_name,activatable_device_state,activatable_device_place,activatable_device_button))
    async def toggle(self,name):
        await self.devices[name].button.click()
        self.devices[name].state = not self.devices[name].state

class Device:
    def __init__(self, name, state, location, button):
        self.name = name
        self.state = state
        self.location = location
        self.button = button
    def __repr__(self):
        return f"Device name = {self.name}, state = {self.state}, location = {self.location}, button = {self.button}"


